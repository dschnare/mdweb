Literate Programming
================

Literate programming is a technique of writing software where the emphasis is on writing source code meant to be consumed by humans rather than a machine. That is, a source code document consists of a document mostly written in a natural language delimited by source code blocks.

This document is in fact a literate program. In fact the *mweave* Python script was produced by running the *mdtangle* script:

    python mdtangle.py -c=mdweave.py -i=readme.md > mdweave.py

 
mdweb - MarkdownWEB Literate Programming Toolkit
================


Overview
----------------------

The **mdweb** toolkit is based on [CWEB](http://sunburn.stanford.edu/~knuth/cweb.html) by Donald Knuth and [noweb](http://www.cs.tufts.edu/~nr/noweb/) by Norman Ramsey. mdweb is written in Python 2.7+ and comes with the following scripts:

- [mdtangle.py](#mdtangle) - A script that will extract source code from a Markdown document.
- [mdweave.py](#mdweave) - A script that will produce nicely formatted and printable documentation from a Markdown document as an HTML file.

A tangled file is any text file that contains documentation written in [Markdown](http://daringfireball.net/projects/markdown/) delimited by code blocks. When untangling a tangled file, all code blocks with a given name will be concatenated together. Code blocks may include other code blocks.

Since Markdown is being used as the preferred format for documentation the [Markdown](http://pypi.python.org/pypi/Markdown/2.1.1) package from the Python Package Index must be installed before running the *mdweave* script.


<h2 id="mdtangle">mdtangle</h2>

    <<mdtangle.py>>=
    <<mdtangle-imports>>
    <<mdtangle-constants>>
    <<mdtangle-untangle>>
    <<mdtangle-load-file>>
    <<mdtangle-code-blocks>>
    <<mdtangle-process-code-blocks>>
    <<mdtangle-include-command>>
    <<mdtangle-include-code-block>>
    <<mdtangle-main>>
    @


### Usage

    python mdtangle.py -c=name-of-code-block -i=path-to-file.md > source-code


### Imports

We import several libraries from the standard Python library. We raise an error if the version of Python is less than 2.7.

    <<mdtangle-imports>>=
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
    @

### Constants

Here several constants are defined that describe several formats used to identify code blocks and the include command. The `CODE_BLOCK_GLUE` is used to concatenate code blocks with the same name. The replacement fields in these constants will be expanded to a code block name.

    <<mdtangle-constants>>=
    CODE_BLOCK_BEGIN = '<<{}>>=\n?'
    CODE_BLOCK_END = '@(?:\n|$)'
    CODE_BLOCK_GLUE = '\n'
    INCLUDE_COMMAND = '^(.*?<<{}>>.*)$'
    @
    

### Untangling

To untangle code blocks from a tangled file we retrieve all code blocks whose `name` equals the specified code block name, from the file specified. Code blocks with the same name will be concatenate. The file will be opened using a UTF-8 character encoding so as to support localized tangled files.

    <<mdtangle-untangle>>=
    def untangle(filename, code_block_name):
      file = load_file_using_utf8(filename)
      code_blocks = get_code_blocks(file, code_block_name)
      code = string.join(code_blocks, CODE_BLOCK_GLUE)
      return code
    @


#### Loading a Tangled File

To load a tangled file we define the `load_file_using_utf8` function that loads a file using the UTF-8 character encoding with a `strict` error mode. Once the file has been synchronously loaded, the BOM is removed if it exists, then the resulting `unicode` object is returned. This function will not catch any exceptions thrown by attempting to open the file. If the file does not exist then an `IOError` is raised, if an encoding error is encountered then a `ValueError` is raised.

    <<mdtangle-load-file>>=
    def load_file_using_utf8(filename):
      file = codecs.open(filename, 'r', 'utf-8', 'strict')
      text = file.read()
      file.close()
      bom = unicode(codecs.BOM_UTF8, 'utf-8')
      text = text.lstrip(bom)
      return text
    @


#### Retrieving Code Blocks

Given `text` and `code_block_name` as arguments the `get_code_blocks` function will attempt to retrieve all code blocks from within the specified `text` whose name equals the value of `code_block_name`. The `text` argument is expected to be either a `unicode` or `str` object. Before retrieving all code blocks the code block pattern is prefixed with a group that captures all leading characters before the start of a code block. This group will be used to trim all leading characters from each line of the code block (i.e. whitespace).

    <<mdtangle-code-blocks>>=
    def get_code_blocks(text, code_block_name):
      begin = CODE_BLOCK_BEGIN.format(re.escape(code_block_name))
      end = CODE_BLOCK_END.format(re.escape(code_block_name))
      pattern = '^(.*?)' + begin + '(.*?)' + end
      groups = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
      return process_code_blocks(text, groups)
    @


#### Processing Code Blocks

When processing code blocks leading characters before a code block is open is stripped from each line in the code block and the include command in run on the code block.

    <<mdtangle-process-code-blocks>>=
    def process_code_blocks(text, groups):
      code_blocks = []
      for leading, code_block in groups:
        leading = len(leading)
        if leading != 0:
          code_block = re.sub('^.{' + str(leading) + '}', '', code_block, flags=re.MULTILINE)
        code_block = run_include_command(text, code_block)
        code_blocks.append(code_block)
      return code_blocks
    @


##### The Include Command

The include command permits code blocks to include other code blocks. It works by searching the specified `text` for code blocks whose name matches the code block name in the command. The name of the code block to include can come from another file if the name has the following format: `file-name:code-block-name`. If the filename is relative it will be resolved relative to the file performing the include. When inserting a code block the entire line containing the command will be replaced with the code block so that all indentation will be preserved for the included code block. 

We start by finding all strings that match the include command pattern. The matched regular expression groups are saved in a list of tuples, where each tuple has the entire line of text at index `[0]` and the code block name to include at index `[1]`.

Next, we iterate over the list of tuples and replace, in the code block, every occurrence of the `command` with the code blocks whose name matches `name` then we return the `code_block`.

    <<mdtangle-include-command>>=
    def run_include_command(text, code_block):
      pattern = INCLUDE_COMMAND.format('([^{}]+?)')
      regexp_groups = re.findall(pattern, code_block, re.MULTILINE)
      for command, name in regexp_groups:
        nested_code_block = include_code_block(text, name)
        code_block = code_block.replace(command, nested_code_block)
      return code_block
    @

To include a code block first we check if the `code_block_name` contains a filename. If a filename is found then the referenced file will be loaded using the UTF-8 character encoding and then the code block will be retrieved from its text. Otherwise, the code block will be retrieved from the `text` of the current tangled file.

    <<mdtangle-include-code-block>>=
    def include_code_block(text, code_block_name):
      pieces = code_block_name.split(':')
      if len(pieces) >= 2:
        path = pieces[0]
        if not os.path.isabs(path): path = os.path.join(os.path.relpath(__file__), path)
        text = load_file_using_utf8(pieces[0])
        code_block_name = string.join(pieces[1:], '')
      return string.join(get_code_blocks(text, code_block_name), CODE_BLOCK_GLUE)
    @


### The main script

The main script creates an argument parser that accepts the following arguments:

- `'-c, '--code-block'` - The name of the code block to retrieve.
- `'-i', '--input'` - The path to the input tangled Markdown file.
- `'-v', '--version'` - The version information.

The arguments `--input` and `--code-block` are passed to the `untangle` function and the result is written to standard output.

    <<mdtangle-main>>=
    parser = argparse.ArgumentParser(description='A Python script that will extract source code from a Markdown document.')
    parser.add_argument('-c', '--code-block', required=True, help='The name of the code block to retrieve.')
    parser.add_argument('-i', '--input', required=True, help='The path to the input tangled Markdown file.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0', help='The version inforamtion.')
    args = parser.parse_args()

    code = untangle(args.input, args.code_block)
    sys.stdout.buffer.write(code.encode('utf-8'))
    @
    
    
<h2 id="mdweave">mdweave</h2>

    <<mdweave.py>>=
    <<mdweave-imports>>
    <<mdweave-main>>
    @


### Usage

    python mdweave.py -i=path-to-file.md -f=html5 > html-document.html


### Imports

Here the standard Python libraries are imported and the `markdown` library.

    <<mdweave-imports>>=
    import markdown
    import argparse
    import re
    @
    
### Main script

The main script creates an argument parser that accepts the following arguments:

- `'-i, --input'` - The name of the Markdown file to process.
- `'-f, --format'` - The output format (xhtml|xhtml1|xhtml5|html|html4|html5)

The `--input` file is read using the UTF-8 character encoding then passed to the `markdown` function for processing. The results are written to standard out.

    <<mdweave-main>>=
    parser = argparse.ArgumentParser(description='A Python script that will produce nicely formatted and printable documentation from a Markdown document as an HTML file.')
    parser.add_argument('-i', '--input', required=True, help='The path to the input Markdown file.')
    parser.add_argument('-f', '--format', default='html5', help='The output format (xhtml|xhtml1|xhtml5|html|html4|html5).')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0', help='The version inforamtion.')
    args = parser.parse_args()

    file = codecs.open(args.input, 'r', 'utf-8')
    text = file.read()
    file.close()
    html = markdown.markdown(text, output_format=args.format)
    sys.stdout.buffer.write(html.encode('utf-8'))
    @