import pandas as pd
import numpy as np
from collections import defaultdict
from slugify import slugify
import re

# Shopify CSV Format https://help.shopify.com/en/manual/products/import-export/using-csv#import-csv-files-into-google-sheets

WC_EXPORT_CSV = 'wc-export.csv'
SHOPIFY_IMPORT_CSV = 'shopify-import.csv'
wc_data = pd.read_csv(WC_EXPORT_CSV)
shopify_data = pd.DataFrame()
# print(wc_data.info)


attribute_keys = wc_data.columns[wc_data.columns.str.endswith(' name')]
attribute_values = wc_data.columns[wc_data.columns.str.endswith('value(s)')]

wc_data_attributes = pd.lreshape(wc_data,{'key':attribute_keys,'value':attribute_values})
wc_data_attributes = wc_data_attributes.pivot(index='ID',columns='key',values='value')

wc_data = pd.merge(wc_data,wc_data_attributes,on='ID')

wc_data['slug'] = wc_data['Name'].apply(lambda x: slugify(x))
wc_data['new_sku'] = wc_data['SKU'].fillna('').apply(
    lambda x: x.split('-')[0]
)
new_wc_data = wc_data[['slug', 'SKU']
                      ].loc[wc_data['Type'] != 'variation']
jointed = wc_data.join(
    new_wc_data.set_index('SKU'), on='new_sku', rsuffix='_other', lsuffix='_original',)
shopify_data['Handle'] = jointed['slug_other']

shopify_data['Title'] = wc_data['Name']
shopify_data['Body (HTML)'] = wc_data['Description']
shopify_data['Vendor'] = wc_data['Manufacturer']

wc_data['new_tags'] = wc_data[['Tags', 'Categories']].fillna(value='').apply(
    lambda x: re.split('>|,', (x['Categories']+x['Tags']).strip()), axis=1)
shopify_data['Tags'] = wc_data['new_tags'].apply(
    lambda x: ','.join(np.unique([y.strip() for y in x])))

published_dict = defaultdict(lambda: 'FALSE')
published_dict[1] = 'TRUE'
shopify_data['Published'] = wc_data['Published'].map(published_dict)

shopify_data['Option1 Name'] = wc_data['Attribute 1 name']
shopify_data['Option1 Value'] = wc_data['Attribute 1 value(s)']
shopify_data['Option2 Name'] = wc_data['Attribute 2 name']
shopify_data['Option2 Value'] = wc_data['Attribute 2 value(s)']
shopify_data['Option3 Name'] = wc_data['Attribute 3 name']
shopify_data['Option3 Value'] = wc_data['Attribute 3 value(s)']
shopify_data['Option1 Name'].loc[shopify_data['Option2 Name'].isna()] = 'Title'
shopify_data['Option1 Value'].loc[shopify_data['Option2 Name'].isna()
                                  ] = 'Default Title'

shopify_data['Variant Price'] = wc_data['Regular price']
shopify_data['Variant Compare At Price'] = wc_data['Sale price']
shopify_data['Variant Requires Shipping'] = 'TRUE'

taxable_dict = defaultdict(lambda: 'FALSE')
taxable_dict['taxable'] = 'TRUE'
shopify_data['Variant Taxable'] = wc_data['Tax status'].map(taxable_dict)

shopify_data['Image Src'] = wc_data['Images']
shopify_data['Image Position'] = 1

# shopify_data['Variant Image'] =
shopify_data['Variant Weight Unit'] = 'lb'

empty_columns = pd.DataFrame(
    columns=[
        'Type',
        'Variant SKU',
        'Variant Grams',
        'Variant Inventory Tracker',
        'Variant Inventory Policy',
        'Variant Fulfillment Service',
        'Variant Barcode',
        'Variant Tax Code',
        'Image Alt Text',
        'Gift Card',
        'SEO Title',
        'SEO Description',
        'Google Shopping / Google Product Category',
        'Google Shopping / Gender',
        'Google Shopping / Age Group',
        'Google Shopping / MPN',
        'Google Shopping / AdWords Grouping',
        'Google Shopping / AdWords Labels',
        'Google Shopping / Condition',
        'Google Shopping / Custom Product',
        'Google Shopping / Custom Label 0',
        'Google Shopping / Custom Label 1',
        'Google Shopping / Custom Label 2',
        'Google Shopping / Custom Label 3',
        'Google Shopping / Custom Label 4',
        'Cost per item'])
shopify_data = pd.concat([shopify_data, empty_columns], axis=1)
print(shopify_data.info)
shopify_data.to_csv(SHOPIFY_IMPORT_CSV, mode='w+')
