import itertools
import os
import urllib

def get_paths(rootdir):
    filepath = set()
    for dir_, _, files in os.walk(rootdir):
        for filename in files:
            reldir = os.path.relpath(dir_, rootdir)
            relfile = os.path.join(reldir, filename)
            filepath.add(relfile)
    return filepath

def replace_all(textarea, dir):
    replace_list = []
    line1 = textarea.split('\n-replace-\n')[1:]
    for i in line1:
        line = i.split('\n-with-\n')
        replace_list.append([line[0], line[1]])
    print(replace_list)   
    # files = list(itertools.chain(*[[os.path.join(root, name) for name in files if '.git' not in root] for root, dirs, files in os.walk('.')]))
    files = get_paths(dir)
    os.chdir(dir)
    for filename in files:
        try:
            with open(filename) as fh:
                all_text = ''
                for i in fh:
                    all_text += i
                print('looked in', filename)
        except:
            continue
        for replace_text in replace_list:
            if replace_text[0] in all_text:
                all_text = all_text.replace(*replace_text)
                with open(filename, 'w') as fh:
                    fh.write(all_text)
                print(''.join(['In', filename,':\nReplaced\n\n', replace_text[0], '\n\nWith:\n\n', replace_text[1], '\n\n\n']))
    os.chdir('..')

def write_lines_to_file(filename, line_list):
    file_lines = []
    if os.path.isfile(filename):
        with open(filename, 'r') as fh:
            for line in fh:
                file_lines.append(line)
    with open(filename, 'w' if not file_lines else 'a') as fh:
        print('Writing to', filename)
        for i, line in enumerate(line_list):
            if line not in file_lines and line + '\n' not in file_lines:
                print(line if not file_lines and i == 0 else '\n' + line)
                fh.write(line if not file_lines and i == 0 else '\n' + line)

if __name__ == '__main__':
    write_lines_to_file('test.txt', ['line1'])
