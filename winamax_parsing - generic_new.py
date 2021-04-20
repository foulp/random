# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import datetime
from getpass import getpass
import os
import pandas as pd
import time
import unicodedata
from webbot import Browser


DATE = datetime.datetime.now()

FILTER = \
f'&history_date_from_day=01&history_date_from_month=10&history_date_from_year=2014\
&history_date_to_day={DATE.day}&history_date_to_month={DATE.month}&history_date_to_year={DATE.year}'

PAGES = ['tournaments', 'sitngo', 'cashgame', 'betting']
TICKETS = {'Etape Live Paris': '0 €', 
			'Starting Block Winamax Poker Tour': '0 €', 
			'Super Freeroll 100K Stade 1': '0 €',
			'Super Freeroll 100K Stade 2': '0 €',
			'Super Freeroll 100K Stade 3': '0 €',
			'Super Freeroll 100K 2017': '0 €',
			'Super Freeroll 100K 2018': '0 €',
			'Super Freeroll 100K 2019': '0 €',
			'Tremplin Winamax Poker Tour': '0 €', 
			'Ticket Finale Départementale Winamax Poker Tour': '0 €',
			'Ticket 2 Million Event': '125 €', 
			'Ticket 2 Million Week Ko': '50 €',
			'Ticket Million Event 15€': '15 €', 
			'Ticket W Pokus Magicus Ko': '15  €',
			'Ticket 0.25€': '0.25 €',
			'Ticket 2€': '2 €', 
			'Ticket 5€': '5 €', 
			'Ticket HIGH FIVE': '5 €',
			'Ticket 10€': '10 €', 
			'Ticket 15€': '15 €', 
			'Ticket 20€': '20 €',
			'Ticket 50€': '50 €',
			'Ticket One Time 15€': '15 €',
			'Ticket COLOSSUS 30€': '30 €',
			'-': '0 €'}
			
web = Browser()
web.go_to('https://www.winamax.fr/account/login.php')

input("Please connect on the opened browser. When finished, press Enter on terminal")

for page in PAGES:
	web.go_to(f'https://www.winamax.fr/account/history.php?to_display={page}{FILTER}&page=1')
	soup = BeautifulSoup(web.get_page_source(), 'html.parser')
	
	form = soup.find('table', {'class': 'no-break-word'})
	if form is None:
		print(f"No records for {page}")
		continue

	pagination = soup.find('div', {'class': 'pagination'})
	if pagination is not None:
		pagination = [v.text for v in pagination.find_all('li')]
		n_pages = int(pagination[pagination.index('Suivant') - 1])
	else:
		n_pages = 1

	columns = [unicodedata.normalize('NFKC', v.text).strip() for v in form.find('thead').find('tr').find_all('th')]
	df = pd.DataFrame(columns=columns)

	for i in range(1, n_pages + 1):
		if i > 1:
			web.go_to(f'https://www.winamax.fr/account/history.php?to_display={page}{FILTER}&page={i}')
			soup = BeautifulSoup(web.get_page_source(), 'html.parser')
			form = soup.find('table', {'class': 'no-break-word'})

		if page != 'betting': 
			table_rows = form.find('tbody').find_all('tr')
		else:
			table_rows = form.find('thead').find_all('tr')
			table_rows = table_rows[3::2]

		for tr in table_rows:
			row = [unicodedata.normalize('NFKC', td.text).strip() for td in tr.find_all('td')]
			if 'En cours' not in row:
				df.loc[df.shape[0]] = row

		print(f'{page} : Page {i} done, df has shape {df.shape[0]}')
		time.sleep(1)

	df.replace(',', '.', regex=True, inplace=True)
	if page in ('sitngo', 'tournaments'):		
		df.loc[:, 'Buy In (€)'] = df['Buy In (€)'].astype(float)
		df['Gain Translated'] = df['Gain'].replace(TICKETS, regex=True).str.replace('[ €]', '').apply(eval)
		df.loc[:, 'Bounty'] = df['Bounty'].str.replace('-', '0 €').str.replace('[ €]', '').astype(float)
		df['Gain Total'] = df['Gain Translated'] + df['Bounty']
		df.loc[:, 'Classement'] = df['Classement'].astype(int)

	if page == 'sitngo':
		df['Benefice'] = df['Gain Total'] - df['Buy In (€)']
		df['Benefice Cumule'] = df['Benefice'].cumsum()
	
	if page == 'tournaments':
		df.loc[:, 'Re-entry/Rebuy'] = df['Re-entry/Rebuy'].replace('', '0').astype(int)
		df['Total Buy In'] = df['Buy In (€)'] * (1 + df['Re-entry/Rebuy'])
		df['Benefice'] = df['Gain Total'] - df['Total Buy In']
		df['Benefice Cumule'] = df['Benefice'].cumsum()
	
	if page == 'cashgame':
		df.loc[:, 'Résultat net (€)'] = df['Résultat net (€)'].astype(float)
		df.loc[:, 'Nb de mains'] = df['Nb de mains'].astype(int)
		df['Nb de mains cumule'] = df['Nb de mains'].cumsum()
		df['Benefice Cumule'] = df['Résultat net (€)'].cumsum()
	
	if page == 'betting':
		df.loc[:, 'Montant (€)'] = df['Montant (€)'].astype(float)
		df.loc[:, 'Gains (€)'] = df['Gains (€)'].astype(float)
		df['Benefice'] = df['Gains (€)'] - df['Montant (€)']
		df['Benefice Cumule'] = df['Benefice'].cumsum()
		
	if df.shape[0]:	
		df.to_csv(os.path.join(os.getcwd(), f'winamax_{page}.csv'), sep=';', index=False, encoding='utf-8-sig')
		print(f'df {page} exported')
	else:
		print(f"df {page} is empty")

print("End of extracting script")
