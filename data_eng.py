import pandas as pd
import fitz
import re
import ollama
from tqdm import tqdm
import pickle
import os


def read_pdf(file_path):
    # Open the PDF file
    document = fitz.open(file_path)
    pdf_text = ""

    # Iterate through each page
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        pdf_text += page.get_text()

    return pdf_text

def remove_page_numbers(text):
    pattern = r"\nPage \d{1,4} of \d{1,4}"

    cleaned_text = re.sub(pattern, "", text)
    
    return cleaned_text

def remove_highlights(text, country_name):
    high_str = country_name+' Highlights 2024  \n '
    text = text.replace(high_str, '')

    return text

def title_finder(text):
    text = text.lstrip()
    pos_title_break = text.split('\n')[0].strip()
    pos_title_dot = text.split(':')[0].strip()
    if len(pos_title_break.split(' ')) <=7:
        return pos_title_break+' - HIGHER'
    elif len(pos_title_dot.split(' ')) <= 7:
        return pos_title_dot+' - SUB'
    else:
        return ""

def parse_text(txt, country_name):
    new_txt = []
    titles = []
    for t in txt:
        new_t = remove_page_numbers(t)
        new_t = remove_highlights(new_t, country_name)
        title = title_finder(new_t)
        titles.append(title)
        new_txt.append(new_t)

    return new_txt, titles

def parse_table(txt):
    new_txt = []

    for t in txt:
        next_txt = ''
        if '\nRates' in t and '%' in t:
            pos_txt = t#.replace('\nRates ', '')
            #pos_txt = pos_txt.replace(' \nRate \n', '')
            more_than_table = pos_txt.split(' \n ')
            if len(more_than_table) > 0:
                if '%' not in more_than_table[-1]:
                    next_txt = more_than_table[-1]
                    pos_txt = ''.join(more_than_table[0:-1])
            
            table_vals = pos_txt.split('\n')
            comp_new_txt = ''
            for i in range(len(table_vals)):
                val = table_vals[i]
                if i < len(table_vals)-1:
                    next_val = table_vals[i+1]
                else:
                    next_val = ''
                
                if '%' in next_val:
                    comp_new_txt += val + ' '
                elif i < len(table_vals) - 2 and i > 0:
                    if '%' in table_vals[i+2]:
                        comp_new_txt += val + '\n'
                    else:
                        comp_new_txt += val + ' '
                else:
                    comp_new_txt += val + '\n'

            if next_txt == '':
                new_txt.append(comp_new_txt)
            else:
                new_txt.append(comp_new_txt)
                new_txt.append(next_txt)
            
        else:
            new_txt.append(t)
    
    return new_txt


def adjust_title(titles):
    higher_area = ""
    cor_title = []
    for i in range(0, len(titles), 1):
        title = titles[i]
        if 'HIGHER' in title:
            adj_name = title.split(' - ')[0]
            higher_area = adj_name
            cor_title.append(adj_name)

        elif 'SUB' in title:
            adj_name = title.split(' - ')[0]
            comp_name = adj_name + ' - '+ higher_area
            cor_title.append(comp_name)
        
        else:
            cor_title.append(cor_title[i-1])
    
    return cor_title

def keyword_generator(p, top=3):
    prompt = "summarize the following paragraph in 3 keywords separated by ,: "+p
    res = ollama.generate(model="phi3", prompt=prompt)["response"]
    return res.replace("\n"," ").strip()

def create_metadata(titles, country, text):
    meta = []

    for title, t in (zip(titles, text)):
        meta_dict = {}

        #keywords = keyword_generator(t)
        if ' - ' in title:
            higher = title.split(' - ')[1]
            sub = title.split(' - ')[0]
            meta_dict['title'] = higher
            meta_dict['subtitle'] = sub
            meta_dict['country'] = country
            #meta_dict['keywords'] = keywords
        else:
            meta_dict['title'] = title
            meta_dict['subtitle'] = title
            meta_dict['country'] = country
            #meta_dict['keywords'] = keywords

        meta.append(meta_dict)
    
    return meta


if __name__ == "__main__":
    files = os.listdir('jurisdictions')
    
    for f in tqdm(files):
        file_path = f'jurisdictions/{f}'
        country_name = file_path.split('/')[1].replace('_summary.pdf', '').replace('_', '/')
        
        text = read_pdf(file_path)
        text = text[:text.find('Contact us:')]

        #text = text.replace('% \n', '')

        text_par = text.split('. \n')   
        if 'Investment basics' in text_par[0]:
            text_par[0] = text_par[0][text.find('Investment basics'):]
        else:
            text_par = text_par[1:]

        
        text_par = parse_table(text_par)
        ptext, ttls = parse_text(text_par, country_name)
        parsed_title = adjust_title(ttls)
        metadata = create_metadata(parsed_title, country_name, ptext)
        text_name = file_path.split('/')[1].replace('summary', 'text')
        meta_name = file_path.split('/')[1].replace('summary', 'meta')

        ids = [country_name+'_'+str(i) for i in range(len(metadata))]
        
        with open(f"texts/{f.replace('.pdf', '')}", "wb") as fp:
            pickle.dump(ptext, fp)
        with open(f"metadata/{f.replace('.pdf', '')}", "wb") as fp:
            pickle.dump(metadata, fp)
        with open(f"ids/{f.replace('.pdf', '')}", "wb") as fp:
            pickle.dump(ids, fp)
    

    
