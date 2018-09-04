#!/usr/bin/env python
from tkinter import filedialog, messagebox
from tkinter import *
import os
from functools import partial

from process import _convert_dataset_to_xls


def browse_button(variable_name):
    input_folder = globals().get(variable_name)
    input_folder.set(filedialog.askdirectory())

def process():
    target = os.path.join(output_folder.get(), output_filename.get())
    _convert_dataset_to_xls(input_folder.get(), target)
    messagebox.showinfo("Dataset processing", "Finished processing, the summary has been saved to {}".format(target))



root = Tk()
root.title('Behaviour data processor')
# root.geometry("600x200")
input_label = Label(master=root, text="Input folder:")
input_label.grid(row=0, column=0)
input_folder = StringVar(value=os.getcwd())
input_folder_entry = Entry(root, text=input_folder)
input_folder_entry.grid(row=0, column=1)

input_browse_button = Button(text="Browse", command=partial(browse_button, variable_name="input_folder"))
input_browse_button.grid(row=0, column=2)

output_label = Label(master=root, text="Output folder:")
output_label.grid(row=1, column=0)
output_folder = StringVar(value=os.getcwd())
output_folder_entry = Entry(root, text=output_folder)
output_folder_entry.grid(row=1, column=1)

output_browse_button = Button(text="Browse", command=partial(browse_button, variable_name="output_folder"))
output_browse_button.grid(row=1, column=2)

output_filename_label = Label(master=root, text="Output filename:")
output_filename_label.grid(row=2, column=0)
output_filename = StringVar(value="summary.xls")
output_filename_entry = Entry(root, textvariable=output_filename)
output_filename_entry.grid(row=2, column=1)

process_button = Button(text="Process", command=process)
process_button.grid(row=4, column=0, columnspan=3, rowspan=2, sticky='nsew')


mainloop()