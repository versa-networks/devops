
import os
import shutil
import time
import argparse



# main function
def main():

    #get input
    parser = argparse.ArgumentParser(description='Script for deleting archive logs on an Analytics node for a given Organization')
    parser.add_argument('--org', default='Provider', type=str,
                        help='Organization Name')
    parser.add_argument('--days', default='30', type=str,
                        help='Number of days back')

    args = parser.parse_args()

    # initializing the count
    deleted_folders_count = 0
    deleted_files_count = 0

    # specify the path
    org = args.org
    path = "/var/tmp/archive/tenant-"+org

    # specify the days
    days = int(args.days)

    # converting days to seconds
    # time.time() returns current time in seconds
    seconds = time.time() - (days * 24 * 60 * 60)
    #print("SECONDS: {}".format(seconds))


    # checking whether the file is present in path or not
    if os.path.exists(path):

        # iterating over each and every folder and file in the path
        for root_folder, folders, main_files in os.walk(path):

            for folder in folders:

                folder_path = os.path.join(root_folder, folder)

                for root_folder_2, folders_2, files in os.walk(folder_path):

                    # checking the current directory files
                    for file in files:

                        # file path
                        file_path = os.path.join(root_folder_2, file)

                        #print("Root Folder: {}".format(file_path))

                        # comparing the days
                        if seconds >= get_file_or_folder_age(file_path):

                            # invoking the remove_file function
                            remove_file(file_path)
                            deleted_files_count += 1 # incrementing count

    else:

        # file/folder is not found
        print("{} is not found".format(path))
        deleted_files_count += 1 # incrementing count

    print("Total folders deleted: {}".format(deleted_folders_count))
    print("Total files deleted: {}".format(deleted_files_count))


def remove_folder(path):

    # removing the folder
    if not shutil.rmtree(path):

        # success message
        print("{} is removed successfully".format(path))

    else:

        # failure message
        print("Unable to delete the {}".format(path))



def remove_file(path):

    # removing the file
    if not os.remove(path):

        # success message
        print("{} is removed successfully".format(path))

    else:

        # failure message
        print("Unable to delete the {}".format(path))


def get_file_or_folder_age(path):

    # getting ctime of the file/folder
    # time will be in seconds
    ctime = os.stat(path).st_ctime

    #print("ctime: {}".format(ctime))

    # returning the time
    return ctime


if __name__ == '__main__':

    main()
