#!/usr/bin/python
import csv
import sys
from datetime import datetime, date

helpful_names = {'credit card pay': 'PAYMENT - THANK YOU'}
total_by_payee = {}
payee_sum = {}
payee_by_category = {}
total_special_occasion = {}
category = {'parking': ['FUCK PARKING TICKETS'],
            'coffee': ['JAVA WORLD ATLANTA GA',
                       'GT STARBUCKS 24018525 ATLANTA GA'],
            'grocery': ['KROGER 346 ATLANTA GA',
                        'WAL-MART #3775 ATLANTA GA'],
            'gas' : ['TEXACO 0370418 ATLANTA GA'],
            'food' : ['GT SUBWAY 24039075 ACWORTH GA',
                      'SQ *BENTO BUS Roswell GA',
                      'GT CHICKFILA 24039331 ATLANTA GA',
                      'Ginya Izakaya ATLANTA GA',
                      'RAKU ATLANTA ATLANTA GA',
                      'FELLINI\'s PIZZA-HOWELL ATLANTA GA',
                      'CHICK-FIL-A #03551 ATLANTA GA',
                      'MCDONALD\'s F10107 ATLANTA GA',
                      'GA TECH PANDA 24416604 ATLANTA GA',
                      'WAFFLE HOUSE 1885 ATLANTA GA',
                      'TIN DRUM ASIACAFE AT G ATLANTA GA',
                      'NOODLE ATLANTA GA',
                      'HIGHLAND BAKERY ATLANTA GA']}
tinder_dates = [{'where': 'VORTEX BAR & GRILL ATLANTA GA',
                 'when': date(2017, 3, 28)},
                {'where': 'RAKU ATLANTA ATLANTA GA',
                 'when': date(2017, 4, 3)},
                {'where': 'AMELIES ATLANTA ATLANTA GA',
                 'when': date(2017, 4, 4)},
                {'where': 'Padriac\'s Atlanta GA',
                 'when': date(2017, 4, 10)}]

class Purchase:
    def __init__(self, purchase_item):
        self.posted_date = datetime.strptime(purchase_item['Posted Date'], '%m/%d/%Y').date()
        self.ref_num = purchase_item['Reference Number']
        self.payee = purchase_item['Payee']
        self.addr = purchase_item['Address']
        self.amount = float(purchase_item['Amount'])
        self.special = self.handle_special()

    def handle_special(self):
        ''' for now only handles tinder dates '''
        for td in tinder_dates:
            if td['where'] == self.payee and td['when'] == self.posted_date:
                return 'tinder'
        return None

def get_category(payee):
    if payee.special is not None:
        return payee.special
    for cat in category:
        for p in category[cat]:
            if payee.payee == p:
                return cat
    return 'misc'

def categorize():
    for payee in total_by_payee:
        if payee == helpful_names['credit card pay']:
            continue
        for purchase in total_by_payee[payee]:
            cat = get_category(purchase)
            if cat in payee_by_category:
                payee_by_category[cat] += purchase.amount
            else:
                payee_by_category[cat] = purchase.amount
    return

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

def get_total_by_payee(filename):
    ''' string (payee) to purchase object dictionary '''
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            purchase = Purchase(row)
            if reader.line_num == 2:
                date_end = purchase.posted_date
            if purchase.payee in total_by_payee:
                total_by_payee[purchase.payee].append(purchase)
            else:
                total_by_payee[purchase.payee] = [purchase]
    date_begin = purchase.posted_date
    return date_begin, date_end

def get_duplicates():
    for payee in total_by_payee:
        if payee not in payee_sum:
            payee_sum[payee] = []
        for purchase in total_by_payee[payee]:
            payee_sum[payee].append(purchase.amount)
    return

def print_payee_amount():
    for payee in payee_sum:
        print('{:s}'.format(payee).ljust(40) + str(payee_sum[payee]))

def get_total():
    total = 0
    for payee in payee_sum:
        if payee == helpful_names['credit card pay']:
            continue
        total += sum(payee_sum[payee])
    return total

def print_summary(date_begin, date_end, total):
    print('\n***** SUMMARY *****')
    print('from {} to {} ({:d} days)'.format(date_begin.strftime('%m/%d/%Y'), \
                                             date_end.strftime('%m/%d/%Y'), \
                                             abs(date_end - date_begin).days))
    print('total spent = {:.2f}'.format(total))


if __name__ == '__main__':
    filename = sys.argv[1]
    date_begin, date_end = get_total_by_payee(filename)
    get_duplicates()
    print_payee_amount()
    categorize()
    print_summary(date_begin, date_end, get_total())
    print_by_category(get_total())
