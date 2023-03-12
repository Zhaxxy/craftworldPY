# def clean_read(fileobj,count=-1):

    # aprevious = fileobj.tell()
    # lehdata = fileobj.read(count)
    # fileobj.seek(aprevious)
    # return lehdata




import io
import hashlib
import os
import platform

def getHash(data):
    m = hashlib.sha1()
    m.update(data)
    return m.digest()

def safe_open(path,fileMode):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, fileMode)

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return int(os.path.getctime(path_to_file))
    else:
        stat = os.stat(path_to_file)
        try:
            return int(stat.st_birthtime)
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return int(stat.st_mtime)

def lbp1_map_splitter(map_data_raw):
    #first 4 bytes is the revision
    revision = map_data_raw.read(4).hex()
    if revision != b'\x00\x00\x01\x00'.hex(): 
        map_data_raw.close()
        raise(Exception('not supported by this parser'))

    bytes_entries = []

    map_data_raw.seek(4)
    #second 4 bytes are the amount of files in the map
    map_count = int.from_bytes(map_data_raw.read(4),"big")

    for _ in range(map_count):
        aprevious = map_data_raw.tell()
        path_length = int.from_bytes(map_data_raw.read(4),"big") #the first 4 bytes before a path is the length of the path
        map_data_raw.seek(aprevious)
        bytes_entries.append(map_data_raw.read(path_length+0x28)) #for this revision, the other data will always be 0x24 (36) long, add the extra 4 for the path length
    map_data_raw.seek(0)
    map_data_raw.seek(4)
    returning_thing = {'Revision':revision,'Count':map_data_raw.read(4).hex(),'Entries':bytes_entries}
    map_data_raw.seek(0)
    return returning_thing

def deseralise_lbp1(entry):
    entry = io.BytesIO(entry)
    format_dict = {'PathLength':0,'Path':'','Timestamp':b'','Size':0,'Hash':b'','Guid':b''}

    format_dict['PathLength'] = int.from_bytes(entry.read(4),'big')
    format_dict['Path'] = entry.read(format_dict['PathLength']).decode()
    format_dict['Timestamp'] = int.from_bytes(entry.read(8),'big')
    format_dict['Size'] = int.from_bytes(entry.read(4),'big')
    format_dict['Hash'] = int.from_bytes(entry.read(0x14),'big')
    format_dict['Guid'] = int.from_bytes(entry.read(),'big')

    return format_dict

def seralise_lbp1(entry):
    a = entry['PathLength'].to_bytes(4,'big')
    b = entry['Path'].encode()
    c = entry['Timestamp'].to_bytes(8,'big')
    d = entry['Size'].to_bytes(4,'big')
    e = bytearray.fromhex(entry['Hash'])
    f = entry['Guid'].to_bytes(4,'big')
    return a + b + c + d + e + f
    
def lbp3_map_splitter(map_data_raw):
    #first 4 bytes is the revision
    revision = map_data_raw.read(4).hex()
    if revision != b'\x01H\x01\x00'.hex(): 
        map_data_raw.close()
        raise(Exception('not supported by this parser'))

    bytes_entries = []

    map_data_raw.seek(4)
    #second 4 bytes are the amount of files in the map
    map_count = int.from_bytes(map_data_raw.read(4),"big")

    for _ in range(map_count):
        aprevious = map_data_raw.tell()
        path_length = int.from_bytes(map_data_raw.read(2),"big") #the first 2 bytes before a path is the length of the path
        map_data_raw.seek(aprevious)
        bytes_entries.append(map_data_raw.read(path_length+0x22)) #for this revision, the other data will always be 0x20 (32) long, add the extra 2 for the path length
    map_data_raw.seek(0)
    map_data_raw.seek(4)
    returning_thing = {'Revision':revision,'Count':map_data_raw.read(4).hex(),'Entries':bytes_entries}
    map_data_raw.seek(0)
    return returning_thing

def deseralise_lbp3(entry):
    entry = io.BytesIO(entry)
    format_dict = {'PathLength':0,'Path':'','Timestamp':b'','Size':0,'Hash':b'','Guid':b''}

    format_dict['PathLength'] = int.from_bytes(entry.read(2),'big')
    format_dict['Path'] = entry.read(format_dict['PathLength']).decode()
    format_dict['Timestamp'] = int.from_bytes(entry.read(4),'big')
    format_dict['Size'] = int.from_bytes(entry.read(4),'big')
    format_dict['Hash'] = int.from_bytes(entry.read(0x14),'big')
    format_dict['Guid'] = int.from_bytes(entry.read(),'big')

    return format_dict

def seralise_lbp3(entry):
    a = entry['PathLength'].to_bytes(2,'big')
    b = entry['Path'].encode()
    c = entry['Timestamp'].to_bytes(4,'big')
    d = entry['Size'].to_bytes(4,'big')
    e = bytearray.fromhex(entry['Hash'])
    f = entry['Guid'].to_bytes(4,'big')
    return a + b + c + d + e + f

  


def get_farc_table(farcfile):
    farcfile.seek(-4,2)
    farc_revision = farcfile.read(4)
    farcfile.seek(0)
    farcfile.seek(-8,2)
    farc_file_count = int.from_bytes(farcfile.read(4),'big')
    
    farcfile.seek(0,2)
    farc_size = farcfile.tell()
    farcfile.seek(0)
    if farc_revision == b'FAR4': tableOffset = farc_size - 0x1c - farc_file_count*0x1c
    elif farc_revision == b'FARC': tableOffset = farc_size - 0x8 - farc_file_count*0x1c
    #elif farc_revision == b'FAR5': tableOffset = farc_size - 0x20 - farc_file_count*0x1c
    else:
        farcfile.close()
        raise Exception('Not a valid or supported farc file')
    farcfile.seek(tableOffset)
    data = farcfile.read()
    farcfile.seek(0)
    return data
    
    