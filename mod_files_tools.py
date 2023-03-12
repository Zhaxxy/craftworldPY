#GUID MODS ARE NOT SUPPORTED!


from tempfile import TemporaryDirectory
import os
import zipfile
import sys




try: import craftworldPY.map_farc_tools as mf
except ModuleNotFoundError: import map_farc_tools as mf


defaultConfig = '''{
  "ID": "sample",
  "type": "pack",
  "title": "A Costume",
  "version": "1.0",
  "author": "Sackthing",
  "description": "No description was provided."
}'''


def compress(files_location,outputfile='Example.zip'):
    # Select the compression mode ZIP_DEFLATED for compression
    # or zipfile.ZIP_STORED to just store the file
    compression = zipfile.ZIP_DEFLATED

    # create the zip file first parameter path/name, second mode
    zf = zipfile.ZipFile(outputfile, mode="w")
    try:
        for subdir, dirs, files in os.walk(files_location):
            for relative_file in files:
                file_name = os.path.join(subdir, relative_file)

                filenameloose = os.path.split(file_name)[-1]
                # Add file to the zip file
                # first parameter file to zip, second filename in zip
                zf.write(file_name, filenameloose, compress_type=compression)

    except FileNotFoundError:
        print("An error occurred")
    finally:
        # Don't forget to close the file!
        zf.close()

def uncompress(filepath,targetdir='mods'):
    with zipfile.ZipFile(filepath,"r") as zip_ref:
        zip_ref.extractall(targetdir)

##################### use the functions below!


def unpack_mod(modfile,location='mods'):
    with TemporaryDirectory() as tempdir:
        uncompress(modfile,tempdir)
        with open(os.path.join(tempdir,'data.map'),'rb') as f:
            mapDict = mf.map2map_dict(f)
        with open(os.path.join(tempdir,'data.farc'),'rb') as f:
            mf.farc2files(f,location,mapDict)


def pack_mod(mod_contentsLoc,modOutput='Example.mod'):
    with TemporaryDirectory() as tempdir:
        mapDict = mf.files2map_dict(mod_contentsLoc)
        mf.files2farc(mod_contentsLoc,os.path.join(tempdir,'data.farc'))
        mf.map_dict2map(mapDict,os.path.join(tempdir,'data.map'))
        with open(os.path.join(tempdir,'config.json'),'w') as f:
            f.write(defaultConfig)
        compress(tempdir,modOutput)

