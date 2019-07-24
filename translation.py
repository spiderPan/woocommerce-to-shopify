# %%
import pandas as pd
import numpy as np
from html2text import unescape

# %%
WC_EXPORT_CSV = 'wc-export/wc-export-product-aw.csv'
wc_full_data = pd.read_csv(WC_EXPORT_CSV)
wc_full_data
# %%
wc_full_data = wc_full_data[['ID', 'SKU', 'Name', 'Description']]
wc_full_data = wc_full_data[~wc_full_data['SKU'].isna()]
is_french = wc_full_data['SKU'].astype(str).str.contains('_fr')
wc_en_data = wc_full_data[~is_french]
wc_fr_data = wc_full_data[is_french]

wc_en_data

wc_fr_data
# %%
wc_fr_data['original_sku'] = wc_fr_data['SKU'].astype(
    str).str.replace('_fr', '')
wc_translation_data = wc_en_data.merge(
    wc_fr_data, left_on=['SKU'], right_on=['original_sku'])

wc_translation_data
# %%
wc_title_translations = wc_translation_data[['Name_x', 'Name_y']]
wc_title_translations.columns = ['source', 'target']
wc_description_translations = wc_translation_data[[
    'Description_x', 'Description_y']].dropna(axis=0)
content_translation = pd.DataFrame()
content_translation['source'] = '<p>' + \
    wc_description_translations['Description_x']+'</p>'
content_translation['target'] = '<p>' + \
    wc_description_translations['Description_y']+'</p>'

wc_description_translations.columns = ['source', 'target']
shopify_langify_import = pd.concat(
    [wc_title_translations, content_translation], ignore_index=True)
shopify_langify_import.drop_duplicates(inplace=True)
shopify_langify_import['source'] = shopify_langify_import['source'].apply(
    lambda x: unescape(x).replace('  ',' '))
shopify_langify_import['target'] = shopify_langify_import['target'].apply(
    lambda x: unescape(x).replace('  ',' '))
# %%
WC_TRANSLATION_CSV = 'translation/shopify-import-langify-aw.csv'
shopify_langify_import.to_csv(WC_TRANSLATION_CSV, mode='w+', index=False)


# %%
