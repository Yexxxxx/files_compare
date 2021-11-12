
import argparse
import hashlib
import os
from filecmp import dircmp


# PRINTING UNIQUE FILES IN EACH FOLDER
def find_unique_files(dcmp):
    uniqueFilesLeft = []
    uniqueFilesRight = []
    # dir1 unique files
    if len(dcmp.left_only) != 0:
        for filename in dcmp.left_only:
            uniqueFilesLeft.append(dcmp.left+"/"+filename)
    # dir2 unique files
    if len(dcmp.right_only) != 0:
        for filename in dcmp.right_only:
            uniqueFilesRight.append(dcmp.right+"/"+filename)
    # recursive call to process the sub folders
    for sub_dcmp in dcmp.subdirs.values():
        sub_uniques = find_unique_files(sub_dcmp)
        uniqueFilesLeft += sub_uniques["left"]
        uniqueFilesRight += sub_uniques["right"]
    uniqueFilesLeft.sort()
    uniqueFilesRight.sort()
    return {"left": uniqueFilesLeft, "right": uniqueFilesRight}


# BUILDING A LIST OF COMMON FILES' PATH INSIDE A FOLDER
def build_common_files(dcmp):
    # listing common files in dir
    commonFiles = []
    for filename in dcmp.common_files:
        commonFiles.append(dcmp.left + "/" + filename)
    # listing in sub-dirs
    for subdir in dcmp.common_dirs:
        subCommonFiles = build_common_files(dircmp(dcmp.left + "/" + subdir, dcmp.right + "/" + subdir))
        for filename in subCommonFiles:
            commonFiles.append(filename)
    commonFiles.sort()
    return commonFiles


# HASHING A FILE, READ BY 16M CHUNKS NOT TO OVERLOAD MEMORY
def hash_file(filepath):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            buf = f.read(0x100000)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()


# PRINTING FILE LIST
def print_unique_files(files):
    if len(files) != 0:
        for filepath in files:
            if os.path.isdir(filepath):
                filepath += '/'
            print("unique: " + filepath)
# GET FILE SIZE
def get_sizeInNiceString(sizeInBytes):
    for (cutoff, label) in [(1024*1024*1024, "GB"),(1024*1024, "MB"),(1024, "KB"),]:
        if sizeInBytes >= cutoff:
            return "%.1f %s" % (sizeInBytes * 1.0 / cutoff, label)
        if sizeInBytes == 1:
            return "1 byte"
        else:
            bytes = "%.1f" % (sizeInBytes or 0,)
    return (bytes[:-2] if bytes.endswith('.0') else bytes) + ' bytes'
    
# THE MAIN FUNCTION
def run_api(dirname_1,dirname_2):
    args = dict(dir1=dirname_1, dir2=dirname_2)
    if not os.path.isdir(args['dir1']):
        print(args['dir1']+ " is not a valid directory")
        exit(-1)
    if not os.path.isdir(args['dir2']):
        print(args['dir2'] + " is not a valid directory")
        exit(-1)
    print("Analyzing directories...")
    dcmp = dircmp(args['dir1'], args['dir2'])
    uniqueFiles = find_unique_files(dcmp)
    print("Building common files list...")
    commonFiles = build_common_files(dcmp)
    relativePathsCommonFiles = []
    for filename in commonFiles:  
        relativePathsCommonFiles.append(filename[len(args['dir1'])+1:])
    filesDifferent = []
    print("Searching for file differences by computing hashes...\n")
    for filepath in relativePathsCommonFiles:
        filepathLeft = args['dir1'] + "/" + filepath
        hashLeft = hash_file(filepathLeft)
        filepathRight = args['dir2'] + "/" + filepath
        hashRight = hash_file(filepathRight)
        if hashLeft != hashRight:
            stringLeft = filepathLeft + "\tsha1: " + hashLeft +"\tsize: "+get_sizeInNiceString(os.path.getsize(filepathLeft))
            stringRight = filepathRight + "\tsha1: " + hashRight +"\tsize: "+get_sizeInNiceString(os.path.getsize(filepathRight))
            filesDifferent.append([filepathLeft, filepathRight])
            print("diff: "+stringLeft)
            print("diff: "+stringRight)
        else:
            os.remove(filepathLeft)
    print_unique_files(uniqueFiles["left"])
    print_unique_files(uniqueFiles["right"])
    if len(filesDifferent)+len(uniqueFiles["left"])+len(uniqueFiles["right"]) == 0:
        print("NO DIFFERENCE FOUND :)\n")


# MAIN ==============================================
# parsing arguments
parser = argparse.ArgumentParser(description="Directories to compare.")
parser.add_argument("--dir1",default="inspection")
parser.add_argument("--dir2",default="standard")
args = parser.parse_args()
if not os.path.isdir(args.dir1):
    print(args.dir1 + " is not a valid directory")
    exit(-1)
if not os.path.isdir(args.dir2):
    print(args.dir2 + " is not a valid directory")
    exit(-1)

# Rough analyse of the two directories
print("Analyzing directories...")
dcmp = dircmp(args.dir1, args.dir2)
uniqueFiles = find_unique_files(dcmp)

# build a common files list
print("Building common files list...")
commonFiles = build_common_files(dcmp)
relativePathsCommonFiles = []
for filename in commonFiles:  # removing the root folder
    relativePathsCommonFiles.append(filename[len(args.dir1)+1:])

# Finding and displaying files that are differents
filesDifferent = []
print("Searching for file differences by computing hashes...\n")
for filepath in relativePathsCommonFiles:
    filepathLeft = args.dir1 + "/" + filepath
    hashLeft = hash_file(filepathLeft)
    filepathRight = args.dir2 + "/" + filepath
    hashRight = hash_file(filepathRight)
    if hashLeft != hashRight:
        stringLeft = filepathLeft + "\t\t\tsha1: " + hashLeft
        stringRight = filepathRight + "\t\t\tsha1: " + hashRight
        filesDifferent.append([filepathLeft, filepathRight])
        print(stringLeft)
        print(stringRight)
    else:
        os.remove(filepathLeft)

# printing unique files
print_unique_files(uniqueFiles["left"])
print_unique_files(uniqueFiles["right"])

if len(filesDifferent)+len(uniqueFiles["left"])+len(uniqueFiles["right"]) == 0:
    print("NO DIFFERENCE FOUND :)\n")
