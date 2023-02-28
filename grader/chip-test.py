import os, shutil, sys, re, zipfile
import subprocess

from penalties import FormattedFeedback
from nand import hardware_simulator, assembler, cpu_emulator, vm_emulator, StudentProgram, \
                 file_generator, jack_compiler
import config
from chardet import detect
import secrets

def read_file(filename):
    with open(filename, 'rb') as f:
        try:
            bytes = f.read()
            return bytes.decode('utf-8').lower()
        except:
            d = detect(bytes)
            return bytes.decode(d['encoding']).lower()

def copy_folder(source, destination, permissions=None):
    shutil.copytree(source, destination, dirs_exist_ok=True)
    #if permissions:
    #    subprocess.run(['chmod', permissions, '-R', destination])


def find_subfolder(folder, file):
    """finds sub-folder which contains a file"""
    for root, f in file_generator(folder):
        if f.lower() == file.lower():
            return root
    return folder


def copy_upwards(folder, extension, correct=[]):
    """ copy files with specific extension from sub-folders upwards
        and fix upper/lower case mistakes """
    for root, f in file_generator(folder):
        if f.split('.')[-1].lower() == extension:
            try:
                #print(f'copying {os.path.join(root, f)} into {folder}')
                shutil.move(os.path.join(root, f), folder)
            except Exception as e:
                print('Exception occurred:')
                print(e)
                pass
            for c in correct:
                if f.lower() == c.lower() + extension and f != c + extension:
                    os.rename(os.path.join(folder, f), os.path.join(folder, c + extension))

def software_project(temp_dir, project_num, t):
    # tests with only one file to translate
    one_file = ['Add', 'Max', 'MaxL', 'Rect', 'Pong'] +\
               ['StaticTest', 'PointerTest', 'BasicTest', 'StackTest', 'SimpleAdd'] +\
               ['BasicLoop', 'FibonacciSeries', 'SimpleFunction']

    if project_num == 6:
        tests = ['Add', 'Max', 'Rect', 'Pong']
        input_extension = '.asm'
        output_extension = '.hack'
    elif project_num == 7:
        tests = ['StaticTest', 'PointerTest', 'BasicTest', 'StackTest', 'SimpleAdd']
        input_extension = '.vm'
        output_extension = '.asm'
        emulator = cpu_emulator
    elif project_num == 8:
        tests = ['BasicLoop', 'FibonacciElement', 'FibonacciSeries', 'NestedCall',
                'SimpleFunction', 'StaticsTest']
        input_extension = '.vm'
        output_extension = '.asm'
        emulator = cpu_emulator
    elif project_num == 10:
        tests = ['ArrayTest', 'Square', 'ExpressionlessSquare']
        output_extension = '.xml'
    else:  # project_num == 11
        tests = ['Average', 'ComplexArrays', 'ConvertToBin', 'Seven']
        input_extension = '.jack'
        output_extension = '.vm'
        emulator = vm_emulator

    feedback = FormattedFeedback(project_num)
    temp_dir = find_subfolder(temp_dir, 'lang.txt')
    if os.path.exists(os.path.join(temp_dir, 'lang.txt')):
        lang = read_file(os.path.join(temp_dir, 'lang.txt'))
    else:
        lang = ''
    if not re.search('file', lang):
        # Delete possible already existing output files
        for root, f in file_generator(temp_dir):
            if f.lower().endswith(output_extension):
                os.remove(os.path.join(root, f))
    elif project_num == 6:
        tests = ['MaxL', 'Rect']
        feedback = FormattedFeedback('6_file')
    copy_folder(os.path.join('grader/tests', 'p' + str(project_num)), temp_dir, permissions='a+rwx')
    program = StudentProgram(temp_dir, project_num)
    return_code, output = program.compile()
    if return_code:
        grade = 0
        feedback = 'Problems encountered in the compilation\n' + output
        return grade, feedback.strip()

    for test in [t]:
        dirname = os.path.join(temp_dir, test)
        filename = os.path.join(dirname, test)
        if test in one_file:
            print(filename + input_extension)
            output = program.run(filename + input_extension)
        else:
            output = program.run(dirname)
        if os.path.exists(dirname + output_extension):
            shutil.move(dirname + output_extension, filename + output_extension)
            feedback.append(test, 'wrong_dir')
        if os.path.exists(test + output_extension):
            shutil.move(test + output_extension, filename + output_extension)
            feedback.append(test, 'wrong_dir')
        if (not os.path.exists(filename + output_extension) and project_num != 11) or \
            (project_num == 11 and not os.path.exists(os.path.join(dirname, 'Main.vm'))):
            print(os.path.join(dirname, 'Main.vm'))
            feedback.append(test, 'file_missing', output)
            continue
        if project_num == 6:
            if not compare_file(filename + '.cmp', filename + output_extension):
                feedback.append(test, 'test_failed',
                                test + output_extension + ' is wrong')
            continue
        output = emulator(temp_dir, test, is_dir=True)
        if len(output) > 0:
            feedback.append(test, 'test_failed', output)

    return feedback.get()

# compare files ignoring whitespace
def compare_file(file1, file2):
    cmp_file = read_file(file1)
    xml_file = read_file(file2)
    return re.sub("\s*", "", cmp_file) == re.sub("\s*", "", xml_file)

def grader(filename, temp_dir, test):
    random_dir = 'temp-' + secrets.token_urlsafe(6)
    temp_dir = os.path.join(temp_dir, random_dir)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)
    os.mkdir(os.path.join(temp_dir, 'src'))
    shutil.copytree(filename, os.path.join(temp_dir,'src'), symlinks=False, ignore=None, ignore_dangling_symlinks=False, dirs_exist_ok=True)
    grade, feedback = software_project(temp_dir, 6, test)
    #shutil.rmtree(temp_dir, ignore_errors=True)
    if feedback == '':
        feedback = 'Congratulations! all tests passed successfully!'
    return grade, feedback


def main():
    if len(sys.argv) < 3:
        print('Usage: python grader.py <dirname> <test>')
        print('For example: python grader.py project3 RAM')
    else:
        temp = os.path.join('grader','temp')
        if not os.path.exists(temp):
            os.mkdir(temp)
        grade, feedback = grader(sys.argv[1], temp , sys.argv[2])
        print(feedback)


if __name__ == '__main__':
    main()
