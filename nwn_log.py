import os
import pandas as pd
import re
import tkinter as tk
from tkinter import Tk, font, filedialog
from PIL import ImageTk, Image
from datetime import datetime


# Text-processing functions

#TBD: Tkinter button & picker option to return summary back to Tkinter pop-up (xp, gold, etc.)

def gold_earned(input_file):
    with open(input_file, 'r') as text_file:
        pattern_gold = r'Acquired\s(\d{1,6})GP'
        output_list = [int(re.search(pattern_gold, line).group(1)) for line in text_file.readlines()
                                                                   if re.search(pattern_gold, line)]
        return str(sum(output_list)) + ' Gold Earned.'


def xp_per_rest(input_file):
    pattern_xp_gained = r'Experience Points Gained\:\s\s(\d{1,4})'
    pattern_bonus_xp = r'Bonus Experience\:\s(\d{1,4})'
    pattern_rest = r'Done resting\.'
    xp_list, final_list = [], []

    with open(input_file, 'r') as text_file:
        for line in text_file.readlines():
            if 'Done resting.' in line and len(xp_list) != 0: # Reset at rest, new cycle starts.
                final_list.append(sum(xp_list))
                xp_list = []
            elif 'Bonus Experience' in line: # Assign - value to bonus, as it will be accounted for, but we want to 0 it.
                xp_list.append(int(re.search(pattern_bonus_xp, line).group(1))*-1)
            elif 'Experience Points Gained:' in line:
                xp_list.append(int(re.search(pattern_xp_gained, line).group(1)))
 
    final_list = '\n'.join([str(i) for i in final_list]) # Convert list elements to string
    
    return print('XP per rest cycle:\n'+final_list+'\n') # Output them in new line with title added


def damage_data(input_file): # Construct 3-element lists (damager, damaged, damage) and build list of lists
    pattern_damager = r'\]\s.*?\]\s(.*)\sdamages'
    pattern_damaged = r'damages\s(.*)\:'
    pattern_damage_done = r'\:\s(\d{1,3})\s\('

    if input_file.endswith('.txt'):
        with open(input_file, 'r') as text_file:
            end_list = [
                [
                    re.search(pattern_damager, line).group(1),
                    re.search(pattern_damaged, line).group(1),
                    re.search(pattern_damage_done, line).group(1)
                ]
                for line in text_file.readlines() if 'damages' in line
            ] 

    return end_list


def construct_df(list_input, cols, dtypes, sort_cols, opt_assign=None):
    if opt_assign:
        df = pd.DataFrame(data=list_input).assign(**opt_assign)
    else:
        df = pd.DataFrame(data=list_input)
    df.columns = cols
    df = df.astype(dtypes)
    df.sort_values(by=sort_cols, ascending=False, inplace=True)
    
    return df


def generate_damage_table(txt_or_folder):
    global damage_df # To utilize DF later on for ad-hoc checks
    if os.path.isdir(txt_or_folder): # Process in loop with 2 extra fields added to DF if a folder is picked
        damage_df = pd.DataFrame()
        for file in os.listdir(txt_or_folder):
            try:
                date = re.search(r'(\d{8})', file).group(1) # yyyymmdd format at start of filename
                quest = re.search(r'\_(.*)\.txt', file).group(1) # From end of filename, following '_'
            except AttributeError:
                date = datetime.now().strftime("%Y%m%d")
                quest = 'N/A'
                
            end_list = damage_data(txt_or_folder+'/'+file) # Call functions create dataset & create DF
            damage_df = damage_df.append(construct_df(end_list, ['damager', 'damaged', 'damage_done', 'date',
                'quest'], {'damage_done':'int', 'date':'datetime64'}, ['quest', 'damage_done'], {'a':date, 'b':quest}))    
                    
    else: # If not a folder, meaning if standalone txt was picked
        end_list = damage_data(txt_or_folder) # Call function to create dataset, then another for df
        damage_df = construct_df(end_list, ['damager', 'damaged', 'damage_done'], {'damage_done':'int'}, 'damage_done')

    if len(end_list) != 0: # Save to excel if the list was not empty, meaning wrong txt was used
        timestamp = datetime.now().strftime("%Y.%m.%d_%H%M%S")
        writer = pd.ExcelWriter(r'./output_files/output_'+timestamp+'.xls')
        damage_df.to_excel(writer, index=False)
        damage_df.groupby(['damager']).sum().sort_values('damage_done', ascending=False).to_excel(writer, startcol=6)
        writer.save()

    return damage_df


# Creating UI with tkinter

app = tk.Tk()

HEIGHT = 500
WIDTH = 889
newsize=(HEIGHT,WIDTH)

C = tk.Canvas(app, height=HEIGHT, width=WIDTH)

# Add background image
try:
    background_image = Image.open(r'./background.gif')
    photo_image = ImageTk.PhotoImage(background_image)
    label = tk.Label(app, image=photo_image)
    label.place(x=0, y=0, relwidth=1, relheight=1)
except:
    None

frame = tk.Frame(app,  bg='#FCF3CF', bd=5)
frame.place(relx=0.5, rely=0.025, relwidth=0.3, relheight=0.1, anchor='n')

get_file_btn = tk.Button(frame, text='Get Txt', font=font.Font(size=10), fg='#FCF3CF', bg='#AF601A', 
                                                        command=lambda: generate_damage_table(filedialog.askopenfilename()))
get_file_btn.place(relx=0.1, relheight=1, relwidth=0.35)
get_folder_btn = tk.Button(frame, text='Get Folder', font=font.Font(size=10), fg='#FCF3CF', bg='#AF601A', 
                                                        command=lambda: generate_damage_table(filedialog.askdirectory(title='Select Folder')))
get_folder_btn.place(relx=0.55, relheight=1, relwidth=0.35)

lower_frame = tk.Frame(app, bg='#641E16', bd=3)
lower_frame.place(relx=0.5, rely=0.6, relwidth=0.75, relheight=0.35, anchor='n')

instr_text ='''
This programme processes NWN log files and saves the output in the "output_files" folder in excel format.

By clicking the "Get Txt" button and selecting a txt log file, you can process a standalone file.

By clicking the "Get Folder" button and selecting a folder, you can process multiple files at once and
also add two extra columns. The recommended file naming convention is "yyyymmdd_quest.txt", for
example "20201231_drider.txt"
'''

instructions = tk.Label(lower_frame, anchor='nw', justify='left', text=instr_text, wraplengt=600)
instructions.config(font=font.Font(size=10), fg='#AF601A', anchor="center", bg='#FCF3CF')
instructions.place(relwidth=1, relheight=1)

C.pack()

if __name__ == '__main__':
    app.mainloop()