import os
import tarfile
import itertools

def dir_to_tarfile(dir,filename='temp.tar',ignore=None):
    os.chdir(dir)
    dirs_files = list(itertools.chain(*[[os.path.join(root, name) for name in dirs + files] for root, dirs, files in os.walk('.')]))
    with tarfile.open('../' + filename, 'w') as tar:
        for name in dirs_files:
            if ignore not in name:
                tar.add(name)
    os.chdir('..')
    #look_in_tar(filename)

def look_in_tar(filename):
    tar = tarfile.open(filename)
    for tarinfo in tar:
        print(tarinfo.name, "is", tarinfo.size, "bytes in size and is", end="")
        if tarinfo.isreg():
            print("a regular file.")
        elif tarinfo.isdir():
            print("a directory.")
        else:
            print("something else.")
    tar.close()

if __name__ == '__main__':
    dir_to_tarfile('hello')