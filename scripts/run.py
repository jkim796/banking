#!/usr/bin/python
import csv
import json
import sys
import argparse
from datetime import datetime, date
import re

helpful_names = {'credit card pay': 'PAYMENT - THANK YOU'}
total_by_payee = {}
payee_sum = {}
payee_by_category = {}
total_special_occasion = {}
category = {}
special_occasions = []
total_by_payee_debit = {}

class Purchase:
    def __init__(self, purchase_item):
        self.date = datetime.strptime(purchase_item['Posted Date'], '%m/%d/%Y').date()
        self.ref_num = purchase_item['Reference Number']
        self.payee = purchase_item['Payee']
        self.addr = purchase_item['Address']
        self.amount = float(purchase_item['Amount'])
        self.special = self.handle_special()
        self.category = self.get_category()

    def handle_special(self):
        for category in special_occasions:
            for item in special_occasions[category]:
                if item['where'] == self.payee and item['when'] == self.date:
                    return category
        return None

    def get_category(self):
        if self.special is not None:
            return self.special
        for cat in category:
            for p in category[cat]:
                if self.payee == p:
                    return cat
                # LYFT payee name changes all the time
                if self.payee[:4] == "LYFT":
                    return "uber"
        return 'misc'


class Debit:
    def __init__(self, item):
        self.date = datetime.strptime(item[0], '%m/%d/%Y').date()
        self.description = item[1] # where the money was spent
        self.amount = float(item[2]) if item[2] != '' else None
        self.balance = float(item[3])


def categorize():
    for payee in total_by_payee:
        if payee == helpful_names['credit card pay']:
            continue
        for purchase in total_by_payee[payee]:
            cat = purchase.get_category()
            if cat in payee_by_category:
                payee_by_category[cat] += purchase.amount
            else:
                payee_by_category[cat] = purchase.amount

def print_by_category(total):
    print('-' * 19)
    print('Expense by Category (from highest to lowest):')
    for category in sorted(payee_by_category, key=payee_by_category.get):
        print('{:s}:'.format(category))
        print('$ {:.2f}'.format(payee_by_category[category]).rjust(20) + \
              '({:.2f} %)'.format(payee_by_category[category] / total * 100).rjust(15))
    print('*' * 19)
    print('TOTAL: $ {:.2f}'.format(total))
    print('*' * 19)

def get_total_by_payee(filename, date_begin, date_end):
    ''' creates a dictionary from payee string to a list of items  '''
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            purchase = Purchase(row)
            if date_end is not None:
                if date_end < purchase.date:
                    continue
            elif reader.line_num == 2:
                date_end = purchase.date
            if date_begin is not None:
                if date_begin > purchase.date:
                    return date_begin, date_end
            if purchase.payee in total_by_payee:
                total_by_payee[purchase.payee].append(purchase)
            else:
                total_by_payee[purchase.payee] = [purchase]
    date_begin = purchase.date
    return date_begin, date_end

def process_debit(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        count = 0
        for row in reader:
            if count == 1:
                match = re.search(r'\d{2}/\d{2}/\d{4}', row[0])
                date_begin = datetime.strptime(match.group(), '%m/%d/%Y').date()
                count += 1
            elif count == 4:
                match = re.search(r'\d{2}/\d{2}/\d{4}', row[0])
                date_end = datetime.strptime(match.group(), '%m/%d/%Y').date()
                count += 1
            elif count > 4:
                break
            else:
                count += 1
        reader.next()
        reader.next()
        for row in reader:
            debit = Debit(row)
            if debit.description in total_by_payee_debit:
                total_by_payee_debit[debit.description].append(debit)
            else:
                total_by_payee_debit[debit.description] = [debit]
    return date_begin, date_end

def print_debit():
    tmp = {}
    for debit in total_by_payee_debit:
        if debit not in tmp:
            tmp[debit] = []
            for item in total_by_payee_debit[debit]:
                tmp[debit].append(item.amount)
    for debit in tmp:
        print('{:s}'.format(debit).ljust(80) + str(tmp[debit]))
    return tmp

def get_duplicates():
    for payee in total_by_payee:
        if payee not in payee_sum:
            payee_sum[payee] = []
        for purchase in total_by_payee[payee]:
            payee_sum[payee].append(purchase.amount)

def print_payee_amount():
    for payee in payee_sum:
        print('{:s}'.format(payee).ljust(40) + str(payee_sum[payee]))

def get_total(tmp):
    total = 0
    for payee in tmp:
        if payee == helpful_names['credit card pay']:
            continue
        total += sum(tmp[payee])
    return total

def print_summary(date_begin, date_end, total):
    print('\n***** SUMMARY *****')
    print('from {} to {} ({:d} days)'.format(date_begin.strftime('%m/%d/%Y'), \
                                             date_end.strftime('%m/%d/%Y'), \
                                             abs(date_end - date_begin).days))
    print('total spent = $ {:.2f}'.format(total))

def init_category(filename):
    global category

    with open(filename, 'r') as f:
        s = f.read()
    category = json.loads(s)

def init_special_occasion(config_file):
    global special_occasions

    with open(config_file, 'r') as f:
        s = f.read()
    special_occasions = json.loads(s)
    for category in special_occasions:
        for item in special_occasions[category]:
            item['when'] = datetime.strptime(item['when'], '%m/%d/%Y').date()


class StatementReader(object):
    def __init__(self, csvfile):
        self.csvfile = csvfile
        self.lines = self.read_csv()

    def read_csv(self):
        with open(self.csvfile, 'r') as f:
            return f.readlines()

    def get_default_start_date(self):
        line = self.lines[-1]
        date = line.split(',')[0]
        return date.replace('/', '.')

    def get_default_end_date(self):
        line = self.lines[1]
        date = line.split(',')[0]
        return date.replace('/', '.')


def main(args):
    init_category('./config/category.json')
    init_special_occasion('./config/special_occasion.json')

    filename = args.csv_file
    filetype = args.type

    reader = StatementReader(filename)
    start_date = reader.get_default_start_date() if args.start_date == '' else args.start_date
    end_date = reader.get_default_end_date() if args.end_date == '' else args.end_date
    date_begin = datetime.strptime(start_date, '%m.%d.%Y').date()
    date_end = datetime.strptime(end_date, '%m.%d.%Y').date()

    if filetype == 'credit':
        date_begin, date_end = get_total_by_payee(filename, date_begin, date_end)
        get_duplicates()
        print_payee_amount()
        categorize()
        print_summary(date_begin, date_end, get_total(payee_sum))
        print_by_category(get_total(payee_sum))
    elif filetype == 'debit':
        date_begin, date_end = process_debit(filename)
        tmp = print_debit()
        print_summary(date_begin, date_end, get_total(tmp))


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Credit/debit card expenditure analyzer.')
    argparser.add_argument('csv_file',
                           help='Transactions CSV file.')
    argparser.add_argument('-t', '--type',
                           default='credit',
                           help='credit | debit | savings')
    argparser.add_argument('-s', '--start_date',
                           default='',
                           help='Start date (m.d.y). Default: earliest date in CSV file.')
    argparser.add_argument('-e', '--end_date',
                           default='',
                           help='End date (m.d.y). Default: latest date in CSV file.')
    args = argparser.parse_args()

    main(args)
