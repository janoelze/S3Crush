import os, commands, string, boto, inspect
from optparse import OptionParser
from boto.s3.key import Key
import time, sys, shutil

OWN_PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
OUTPUT_PATH = '/S3Crush/'
FINISHED_PATH =  OWN_PATH + OUTPUT_PATH
FILES_QUEUE = []
OPTIMIZED_FILES = 1
ALL_FILES = 0
BUCKET = ''
ACCESSKEY = ''
SECRET = ''

def getOpts():
  parser = OptionParser()
  parser.add_option("-b", "--bucket", dest="bucket", help="The S3-Bucket you want to crush", metavar="BUCKET")
  parser.add_option("-s", "--secret", dest="secret", help="Your Amazon S3 Secret", metavar="SECRET")
  parser.add_option("-a", "--accesskey", dest="accesskey", help="Your Amazon S3 Access Key", metavar="ACCESSKEY")
  return parser.parse_args()

def out(m):
  print '** ' + str(m)

def setupDeps():
  if not os.path.exists(FINISHED_PATH):
    os.makedirs(FINISHED_PATH)
  else:
    shutil.rmtree(FINISHED_PATH)
    os.makedirs(FINISHED_PATH)

def download(f,file_path,file_name):
  f.get_contents_to_filename(file_path)
  return True

def optimize(file_path,file_name):
  output = commands.getoutput('optipng %s' % (file_path))
  return True

def get_result(initital_size,optimized_size):
  d = str(initital_size-optimized_size)
  p = str(round(100-((1.0 * optimized_size / initital_size) * 100),2))
  return d,p

def upload_files(method):
  global BUCKET

  files = []
  for file_name in os.listdir(FINISHED_PATH):
    if file_name.endswith('.PNG') or file_name.endswith('.png'):
      files.append(file_name)
  
  conn = boto.connect_s3(opts.accesskey,opts.secret)
  bucket = conn.create_bucket(BUCKET)

  i = 1
  for file_name in files:
    out(str(i)+'/'+str(len(files))+' | Uploading: '+file_name)
    k = Key(bucket)

    if method == 'overwrite':
      k.key = file_name
    elif method == 'prefix':
      k.key = 'opt_'+file_name
    elif method == 'newdir':
      k.key = 'S3crush/'+file_name

    k.set_contents_from_string(open(FINISHED_PATH+file_name,'r').read())
    out(str(i)+'/'+str(len(files))+' | -> Upload finished: '+file_name)
    i += 1

def start_files_queue(FILES_QUEUE):
  global OPTIMIZED_FILES
  i = 0
  for f in FILES_QUEUE:
    file_name = f.key
    file_path = FINISHED_PATH+file_name
    out(str(i)+'/'+str(len(FILES_QUEUE))+' | Downloading: '+file_name)
    if download(f,file_path,file_name):
      initital_size = os.path.getsize(file_path)
      out(str(i)+'/'+str(len(FILES_QUEUE))+' | Optimizing: '+file_name)
      if optimize(file_path,file_name):
        optimized_size = os.path.getsize(file_path)
        OPTIMIZED_FILES = (OPTIMIZED_FILES + 1)
        (d,p) = get_result(initital_size,optimized_size)
        out(str(i)+'/'+str(len(FILES_QUEUE))+' | -> OptiPNG finished: Saved '+d+' bytes ('+p+' %) \n')
        i += 1

def get_files(opts):
  global ALL_FILES
  conn = boto.connect_s3(opts.accesskey,opts.secret)
  bucket = conn.get_bucket(BUCKET)
  for f in bucket.list():
    file_name = f.key
    file_path = FINISHED_PATH+file_name
    if file_name.endswith('.PNG') or file_name.endswith('.png'):
      if not os.path.exists(file_path):
        ALL_FILES = (ALL_FILES + 1)
        FILES_QUEUE.append(f)
  return FILES_QUEUE

def fin():
  print '\n** S3Crush finished optimizing your Bucket. What now?'
  print '** 1.) Overwrite the files in the Bucket with its optimized version.'
  print '** 2.) Upload the optimized version with a "opt_"-prefix.'
  print '** 3.) Upload the optimized version to a new folder in your Bucket.'
  print '** 4.) Do nothing.'
  c = input('Pick a number: ')
  
  if c == 1:
    upload_files('overwrite')
  elif c == 2:
    upload_files('prefix')
  elif c == 3:
    upload_files('newdir')
  elif c == 4:
    pass
  else:
    print 'Hm?'

if __name__ == '__main__':
  (opts, args) = getOpts()
  setupDeps()
  BUCKET = opts.bucket
  FILES_QUEUE = get_files(opts)
  start_files_queue(FILES_QUEUE)
  fin()