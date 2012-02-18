import sys

if sys.version_info < (2, 7):
  raise 'Must use Python 2.7 or greater.'

import codecs
import re
import string
import os
import argparse

if sys.version_info.major >= 3:
  unicode = str
  string.join = lambda string, sep: sep.join(string)

CODE_BLOCK_BEGIN = '^([^\n\r\f]*?)<<{}>>=\n?'
CODE_BLOCK_END = '@(?:\n|$)'
CODE_BLOCK_GLUE = '\n'
INCLUDE_COMMAND = '^(.*?<<{}>>.*)$'

def untangle(filename, code_block_name):
  file = load_file_using_utf8(filename)
  code_blocks = get_code_blocks(file, code_block_name)
  code = string.join(code_blocks, CODE_BLOCK_GLUE)
  return code

def load_file_using_utf8(filename):
  file = codecs.open(filename, 'r', 'utf-8', 'strict')
  text = file.read()
  file.close()
  bom = unicode(codecs.BOM_UTF8, 'utf-8')
  text = text.lstrip(bom)
  return text

def get_code_blocks(text, code_block_name):
  begin = CODE_BLOCK_BEGIN.format(re.escape(code_block_name))
  end = CODE_BLOCK_END.format(re.escape(code_block_name))
  pattern = begin + '(.*?)' + end
  groups = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
  return process_code_blocks(text, groups)

def process_code_blocks(text, groups):
  code_blocks = []
  for leading, code_block in groups:
    leading = len(leading)
    if leading != 0:
      code_block = re.sub('^.{' + str(leading) + '}', '', code_block, flags=re.MULTILINE)
    code_block = run_include_command(text, code_block)
    code_blocks.append(code_block)
  return code_blocks

def run_include_command(text, code_block):
  pattern = INCLUDE_COMMAND.format('([^{}]+?)')
  regexp_groups = re.findall(pattern, code_block, re.MULTILINE)
  for command, name in regexp_groups:
    nested_code_block = include_code_block(text, name)
    code_block = code_block.replace(command, nested_code_block)
  return code_block

def include_code_block(text, code_block_name):
  pieces = code_block_name.split(':')
  if len(pieces) >= 2:
    path = pieces[0]
    if not os.path.isabs(path): path = os.path.join(os.path.relpath(__file__), path)
    text = load_file_using_utf8(pieces[0])
    code_block_name = string.join(pieces[1:], '')
  return string.join(get_code_blocks(text, code_block_name), CODE_BLOCK_GLUE)

parser = argparse.ArgumentParser(description='A Python script that will extract source code from a Markdown document.')
parser.add_argument('-c', '--code-block', required=True, help='The name of the code block to retrieve.')
parser.add_argument('-i', '--input', required=True, help='The path to the input tangled Markdown file.')
parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0', help='The version inforamtion.')
args = parser.parse_args()

code = untangle(args.input, args.code_block)
if sys.version_info.major >= 3:
  sys.stdout.buffer.write(code.encode('utf-8'))
else:
  sys.stdout.write(code.encode('utf-8'))