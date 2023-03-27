#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A new and modern shell

Should work the same on Windows, Linux and Mac. Uses Jupyter-console as base

# TODO: https://pypi.org/project/prettytable/

1. Om du har en lång körning på flera filer (exempel: convert *.mp4) då skall det i efterhand lätt gå att se vilka filer som är färdiga och vilka som är kvar att jobba på.
1.1 Medans denna långa körning pågår så skall det gå att gå in och ändra i kön ifall en vill prioritera om filer, ta bort eller lägga till.
2. Om du skriver ett långt kommando men inte riktigt minns hur det skall vara så kan du när som helst skriva '?' för att få hjälpen och sedan få kommandot tillbaka till prompten så du kan fortsätta skriva.
3. Det skall gå att "select multiple files" med ett kommando som t.ex. 'select *.mp4' och sedan 'select *.webm'. Dessa filer som nu är valda skall enkelt gå att se i en lista till höger. Det skall gå att ta bort filer ur den listan också.
4. Varje console skall ha en backend och en foreground så att en kan använda det som SSH samt att det går att disconnecta utan att allt du håller på med dör.
5. Snabbknappar, F1 - F12 men kanske även andra
6. Massor av "choice.com" där du har val att göra men om du inte gör något val inom 30 sekunder så väljer console åt dig.
7. Om console förstår commandot men det kräver sudo så skall du kunna bara fortsätta med sudo istället för att skriva om
8. Web interface? Fördel är att HTML har väldigt välutvecklad grafiska element.
9. Enkelt kunna pausa en lång körning och sedan ställa in när den skall fortsätta. 
10. Delete file skall märka filen som "can be taken away" (lite som papperskorgen).
11. Det skall funka BRA på Windows, Linux, Mac
12. Enkelt att plugga in andra språk, som t.ex. python
"""

from __future__ import annotations

__version__ = 230324221954
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"

import typing as _typing
import os
import pathlib
import re
import json
import numpy as np
import harding_utils as hu
import time

use_natsort = True
try:
    import natsort
except ImportError:
    use_natsort = False
    hu.log_print("WARNING: Module natsort not installed, this module is not required but strongly recommended. pip install natsort", arg_type="WARNING")

use_prettytable = True
try:
    import prettytable
except ImportError:
    use_prettytable = False
    hu.log_print("WARNING: Module prettytable not installed, this module is not required but strongly recommended. pip install prettytable", arg_type="WARNING")

def _repr_type_str(arg_object: _typing.Any) -> str:
    ''' Generic repr function that types the type and then the str(object) '''
    return f"{type(arg_object)} which has str(self):\n{str(arg_object)}"

class _files:
    _selected: _typing.List[str] = []
    
    def __init__(self, arg_file_pattern: _typing.Union[str, pathlib.Path, _typing.List[str], None] = None, arg_recursive: bool = False, arg_supress_errors: bool = False, arg_debug: bool = False):
        setattr(_files, '__call__', self.select)
        self.select(arg_file_pattern)

    def clear(self) -> int:
        ''' Clears the selected files '''
        self._selected = []
        return 0

    def select(self, arg_file_pattern: _typing.Union[str, pathlib.Path, _typing.List[str], None] = None, arg_recursive: bool = False, arg_supress_errors: bool = False, arg_debug: bool = False) -> int:
        ''' Makes a new selection of files (clear the old selection) and returns the number of files added '''
        
        self.clear()
        if arg_file_pattern is None:
            return 0
        if isinstance(arg_file_pattern, pathlib.Path):
            arg_file_pattern = str(arg_file_pattern)

        if isinstance(arg_file_pattern, str) and arg_file_pattern.startswith('http'):
            _new_files = [arg_file_pattern]
        else:
            _new_files = hu.adv_glob(arg_paths=arg_file_pattern, arg_recursive=arg_recursive, arg_supress_errors=arg_supress_errors, arg_debug=arg_debug)
        self._selected.extend(_new_files)
        self.sort()
        return len(_new_files)

    def sort(self, arg_sort_by: str = "alphabetical"):
        ''' Sort the files in alhpabetic order.
            
            TODO: Parameter arg_sort_by can be 1 of the following strings: "alphabetical", "size", "extension"  
        
        '''
        del arg_sort_by # TODO: Not implemented yet
        self._selected = np.unique(self._selected)
        if use_natsort:
            self._selected = natsort.natsorted(self._selected)

    def __add__(self, arg_adding: _typing.Union[str, pathlib.Path, _typing.List[str], _files]) -> _files:
        if isinstance(arg_adding, pathlib.Path):
            arg_adding = str(arg_adding)

        if isinstance(arg_adding, (list, str)):
            _new_files = hu.adv_glob(arg_paths=arg_adding)
            self._selected.extend(_new_files)
        elif isinstance(arg_adding, _files):
            self._selected.extend(_files._selected)
        else:
            raise ValueError(f'Cannot add {type(arg_adding)}')
        return self

    def __sub__(self, arg_subing: _typing.Union[str, pathlib.Path, _typing.List[str], _files]) -> _files:
        if isinstance(arg_subing, pathlib.Path):
            arg_subing = str(arg_subing)

        if isinstance(arg_subing, (list, str)):
            _files_to_remove = hu.adv_glob(arg_paths=arg_subing)
        elif isinstance(arg_subing, _files):
            _files_to_remove = arg_subing._selected
        else:
            raise ValueError(f'Cannot sub {type(arg_subing)}')
        
        self._selected = [file for file in self._selected if file not in _files_to_remove]
        return self

    def prioritize(self, arg_file: _typing.Union[str, pathlib.Path]):
        ''' Put this file first in the list '''
        try:
            self._selected.insert(0, self._selected.pop(self._selected.index(arg_file)))
        except ValueError as exc:
            log_print(f"Could NOT find the file '{arg_file}'", arg_type="WARNING")

    def remove_by_regexp(self, arg_regexp: str, arg_regexp_flags: int = re.IGNORECASE) -> int:
        ''' If you have a large selection of files and want to remove some of them
            
            Returns the number of files that matched and was removed
        '''
        
        try:
            _regexp = re.compile(arg_regexp, flags=arg_regexp_flags) # most useful is probable re.IGNORECASE
        except re.error as regexp_error:
            hu.log_print(f"Error in the regexp: {regexp_error}. You wrote: '{arg_regexp}'", arg_type="ERROR")
            return 0

        _len_before = len(self._selected)
        self._selected = [file for file in self._selected if not _regexp.fullmatch(file)]
        return _len_before - len(self._selected)

    def save_selection_to_file(self, arg_filename: _typing.Union[str, pathlib.Path], arg_as_json: bool = False) -> bool:
        ''' Save the current file dict to a file '''
        if arg_as_json:
            return hu.dict_dump_to_json_file(arg_dict=self._selected, arg_filename=str(arg_filename))
        return hu.text_write_whole_file(arg_filename=str(arg_filename), arg_text='\n'.join(self._selected))

    def load_selection_from_file(self, arg_filename_or_url: _typing.Union[str, pathlib.Path]) -> int:
        ''' If you have a file saved with each row is a full file path, then this can load that.
            If you have a file that looks ALMOST like a file list then you can use the argument arg_regexp
            to pick out the filename on each line. Default is to use the whole line.

            Returns the number of files that is in the file dict after we loaded the file
        '''

        
        _whole_file = hu.text_read_whole_file(arg_filename_or_url=str(arg_filename_or_url))
        if not _whole_file:
            return self.clear()
        if self._json_set(_whole_file):
            return len(self._selected)
        else:
            hu.log_print(f"Failed to parse '{arg_filename_or_url}' as JSON", arg_type="ERROR")
        
        self._selected = hu.list_from_str(_whole_file, arg_re_splitter='[\n]|[\r]')
        return len(self._selected)

    def _json_get(self) -> str:
        return hu.dict_to_json_string_pretty(self._selected)

    def _json_set(self, arg_json: str) -> bool:
        ''' Try to parse the input str as JSON and validate that it's a list
            
            Returns False if the parsing failed, returns True if everything is ok
        '''
        try:
            _tmp_list = json.loads(arg_json)
            if not _tmp_list or not isinstance(_tmp_list, list) or not isinstance(_tmp_list[0], str):
                log_print(f"File is not a valid file list", arg_type="ERROR")
                raise ns.json.JSONDecodeError
        except:
            return False
        
        self._selected = _tmp_list
        return True

    json = property(fget=_json_get, fset=_json_set, doc='Handle the selected files as a JSON str')

    def table(self, arg_with_stats: bool = False) -> bool:
        ''' Print the files as a table '''
        if not use_prettytable:
            log_print("You do NOT have prettytable installed. pip install prettytable", arg_type="ERROR")
            return False
        
        _table = prettytable.PrettyTable()
        _table.field_names = ["Filename", "Size", "Created", "Modified"] # TODO: Add support for showing filesize and created date?
        _table.align["Filename"] = "l"
        _table.align["Size"] = "r" 
        
        _table.add_rows([[file, 0, 'TODO:', 'TODO:'] for file in self._selected])
        print(f"[{hu.now_nice_format()}]")
        print(_table)
        return True

    def system(self, arg_command: str = '', arg_dry_run: bool = False) -> bool:
        ''' Run os.system() on all files. Use the string %file in the command to replace this by the filename 
        
            Set the argument arg_dry_run to True to see the commands that would be executed without actually executing them.
        '''
        for file in self._selected:
            _command = arg_command.replace('%file', f'"{file}"')
            
            hu.log_print(f"Running command:  {hu.console_color(_command, arg_color='OKBLUE')}", arg_type="DRYRUN", arg_force_flush=True)
            time.sleep(0.1)
            if not arg_dry_run:
                os.system(_command)
                
        return True

    def __len__(self) -> int:
        return len(self._selected)

    def __iter__(self) -> _typing.Iterator:
        return iter(self._selected)

    def __next__(self, arg_iterator: _typing.Iterator) -> str:
        return next(arg_iterator)
   
    def __str__(self) -> str:
        return self._json_get()

    def __repr__(self) -> str:
        return _repr_type_str(self)

files = _files()

class _ls:
    _last_ls: _files = _files()
    
    def __init__(self, arg_pattern: _typing.Union[str, None] = None):
        pass

    __call__ = _last_ls.select
    def list_files(self, arg_file_pattern: _typing.Union[str, pathlib.Path, _typing.List[str], None] = None, arg_recursive: bool = False, arg_supress_errors: bool = False, arg_debug: bool = False) -> int:
        if not arg_file_pattern:
            arg_file_pattern = '*'
        self._last_ls.select(arg_file_pattern=arg_file_pattern, arg_recursive=arg_recursive, arg_supress_errors=arg_supress_errors, arg_debug=arg_debug)
        hu.timestamped_print(str(self._last_ls))
    
    def __repr__(self) -> str:
        function_name = ""
        try:
            info = hu._file_and_line_number(18)
            function_name = f"{os.path.splitext(os.path.basename(info.filename))[0]}.{info.function}"
            if function_name == "ipkernel.do_execute":
                hu.log_print("We are in Jupyter")
        except: 
            pass
        
        
        
        
        
        
        
        self._last_ls = _files('asdasda')
        return "\n".join(self._last_ls)
ls = _ls()

def cwd(arg_new_current_working_directory: _typing.Union[str, pathlib.Path, None] = None) -> pathlib.Path:
    ''' Gets (or sets) the current working directory '''
    if arg_new_current_working_directory:
        if arg_new_current_working_directory == home:
            os.chdir(home())
        else:
            os.chdir(str(arg_new_current_working_directory))
    return pathlib.Path.cwd()

cd = cwd # TODO: Is this a bad idea? Linux user will not like that cd doesn't take them to home

def home() -> pathlib.Path:
    ''' Get the users home directory '''
    return pathlib.Path.home()

# TODO: def copy()
# TODO: def move()
# TODO: def dir() # Det skall gå att hänvisa till en ls för att lägga till i selected
# TODO: def del()
# TODO: def os.system()

if __name__ == "__main__":
    print("This is part of neoshell and is not suppose to be used from the command line")
