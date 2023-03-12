import os
import sys

try: from internal_map_farc_tools import *
except ModuleNotFoundError: from craftworldPY.internal_map_farc_tools import *

#Theese functions you actually use!
def map2map_dict(map_file_object,guid_sort=False):
    revision = map_file_object.read(4).hex()
    map_file_object.seek(0)
    if revision == b'\x01H\x01\x00'.hex():
        nice_data = lbp3_map_splitter(map_file_object)
        for index, entry in enumerate(nice_data['Entries']):
            nice_data['Entries'][index] = deseralise_lbp3(entry)
        if guid_sort:
            nice_data['Entries'].sort(key=lambda d: d[guid_sort])
            return nice_data
        else: return nice_data
    elif revision == b'\x00\x00\x01\x00'.hex():
        nice_data = lbp1_map_splitter(map_file_object)
        for index, entry in enumerate(nice_data['Entries']):
            nice_data['Entries'][index] = deseralise_lbp1(entry)
        if guid_sort:
            nice_data['Entries'].sort(key=lambda d: d[guid_sort])
            return nice_data
        else: return nice_data
    else:
        map_file_object.close()
        raise(Exception('not supported by this parser'))
        
        
def map_dict2map(TheMapDict,output_file):
    if TheMapDict['Revision'] == b'\x01H\x01\x00'.hex():
        for index, each in enumerate(TheMapDict['Entries']):
            TheMapDict['Entries'][index] = seralise_lbp3(TheMapDict['Entries'][index])
    elif TheMapDict['Revision'] == b'\x00\x00\x01\x00'.hex(): 
        for index, each in enumerate(TheMapDict['Entries']):
            TheMapDict['Entries'][index] = seralise_lbp1(TheMapDict['Entries'][index])
    else:
        raise(Exception('not supported by this parser'))
    with open(output_file,'wb') as fone: fone.write(bytearray.fromhex(TheMapDict['Revision'])+bytearray.fromhex(TheMapDict['Count']))
    with open(output_file,'ab') as f:
        for each in TheMapDict['Entries']: f.write(each)

def files2farc(files_location,output_farc,revision=b'FAR4'):
    farc_table = []
    file_count = 0
    with open(output_farc,'w') as _: pass #dels the file
    with open(output_farc,'ab+') as farc_append:
        for subdir, dirs, files in os.walk(files_location):
            for relative_file in files:
                file = os.path.join(subdir, relative_file)
                file_count += 1
                with open(file,'rb') as f: 
                    data = f.read()
                    f.seek(0,2)
                    file_size = f.tell().to_bytes(4,'big')
                farc_append.seek(0,2)
                offset = farc_append.tell().to_bytes(4,'big')
                hhash = getHash(data)
                farc_table.append(hhash+offset+file_size)
                farc_append.write(data)
        farc_append.write(b''.join(farc_table))

        if revision == b'FAR4':
            some_hash = b'\x00'*20 #idk what this is meant to be, i think its a hash but not sure, yes i have looked! so i just use an empty hash which should be fine
            farc_append.write(some_hash+file_count.to_bytes(4,'big')+revision)
        elif revision == b'FARC':
            farc_append.write(file_count.to_bytes(4,'big')+revision)
        else: 
            raise(Exception(f'{revision.encode()} is not supported by this parser'))
            
            
def farc2files(farc_file_object,output_location,mapdict=False,useFileExtensions=True, sltOutputFILE=False):
    if useFileExtensions:
        file_extensions = {
b'LVLb':'.bin',
b'\x89PNG':'.png',
b'PLNb':'.plan',
b'TEX ':'.tex',
b'MATb':'.mat',
b'GMTb':'.gmat',
b'MSHb':'.mol',
b'PALb':'.pal',
b'DLCt':'.dlc',
b'FNTb':'.fnt',
b'QSTb':'.qst',
b'BIKi':'.bik',
b'FSB4':'.fsb',
b'JNTb':'.joint',
b'SMHb':'.smh',
b'SLTb':'.slt'
}
    else: file_extensions = {}
    
    farc_offset_table = get_farc_table(farc_file_object)
    farc_revision = farc_offset_table[-4:]
    farc_file_count = int.from_bytes(farc_offset_table[-8:][:-4],'big')
    farc_offset_table = io.BytesIO(farc_offset_table)
    if farc_revision != b'FAR4' and farc_revision != b'FARC': raise(Exception('not supported by this parser'))
    if not mapdict:    
        for _ in range(farc_file_count):
            data = farc_offset_table.read(0x1c)
            hhash = data[:0x14].hex()
            ooffset = int.from_bytes(data[0x14:][:4],'big')
            ssize = int.from_bytes(data[24:][:4],'big')
            farc_file_object.seek(ooffset)
            farc_file_contents = farc_file_object.read(ssize)
            farc_file_object.seek(0)
            if farc_file_contents[:4] == b'SLTb' and sltOutputFILE:
                with open(sltOutputFILE,'wb') as noename: noename.write(farc_file_contents)
                continue
            try: custom_name = hhash + file_extensions[farc_file_contents[:4]]
            except KeyError: custom_name = hhash
            with open(os.path.join(output_location,custom_name),'wb') as noename: noename.write(farc_file_contents)
            
    else:
        for _ in range(farc_file_count):
            data = farc_offset_table.read(0x1c)
            hhash = int.from_bytes(data[:0x14],'big')
            ooffset = int.from_bytes(data[0x14:][:4],'big')
            ssize = int.from_bytes(data[24:][:4],'big')
            ppath = list(filter(lambda path: path['Hash'] == hhash, mapdict['Entries']))[0]['Path']
            farc_file_object.seek(ooffset)
            farc_file_contents = farc_file_object.read(ssize)
            farc_file_object.seek(0)
            if farc_file_contents[:4] == b'SLTb' and sltOutputFILE:
                with open(sltOutputFILE,'wb') as noename: noename.write(farc_file_contents)
                continue
            with safe_open(os.path.join(output_location,ppath),'wb') as named_file:
                farc_file_object.seek(ooffset)
                named_file.write(farc_file_object.read(ssize))
                farc_file_object.seek(0)                


def files2map_dict(files_location,revision='01480100',guids=False):
    if revision != b'\x01H\x01\x00'.hex() and revision != b'\x00\x00\x01\x00'.hex(): raise(Exception('not supported by this parser'))
    guid_start = 1441792
    fileDB_mapdict = {'Revision':revision,'Count':0,'Entries':[]}
    if guids: raise NotImplementedError('Cant give your own guids right now, this was mainly for .mod files for profiles which dont use guids anyways')
    file_count = 0
    for subdir, dirs, files in os.walk(files_location):
        for relative_file in files:
            file_count += 1
            file = os.path.join(subdir, relative_file)
            path = file.replace(files_location,'')
            path = path.replace('\\','/')
            if path.startswith('/'): path = path[1:]
            with open(file,'rb') as f:
                data = f.read()
                f.seek(0)
                format_dict = {'PathLength':0,'Path':'','Timestamp':b'','Size':0,'Hash':b'','Guid':b''}
                format_dict['Hash'] = getHash(data).hex()
                format_dict['PathLength'] = len(path)
                format_dict['Path'] = path
                format_dict['Timestamp'] = creation_date(file)
                f.seek(0,2)
                format_dict['Size'] = f.tell()
                f.seek(0)
                guid_start += 1
                format_dict['Guid'] = guid_start
                fileDB_mapdict['Entries'].append(format_dict)
    fileDB_mapdict['Count'] = (file_count).to_bytes(4,'big').hex()
    return fileDB_mapdict





if __name__ == '__main__': 
    print("Supported revisions are 00000100 (LBP1 and LBP2) and 01480100 (LBP3). LBP Vita is bassiclly the lbp1 revision, its just that it supports files with no names")