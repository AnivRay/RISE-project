import os
import Analyzer


def main():
    '''
    folders = []
    for (dirname, dirs, files) in os.walk("C:\\Users\\anivr\\Desktop\\AutoDownload"):
        folders = dirs
        for x, f in enumerate(folders):
            folders[x] = dirname + "\\" + f
        break
    for folder in folders:
        print("FOLDER : " + str(folder))
        print("===================================")
        # print(str(folder))
        try:
            Analyzer.main(folder)
        except Exception as err:
            print("There was an error : " + "[" + str(folder) + "]" + str(err))
    print(str(Analyzer.S / (Analyzer.S + Analyzer.F)))
    '''
    Analyzer.main("C:\\Users\\anivr\\Desktop\\AutoDownload\\service.subtitles.opensubtitles\\service.py")





main()
