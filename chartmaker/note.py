import requests
vars ='{"variables":{"x_axis":"col_1","y_axis":"col_1","value":"None","agg":"count","facet_col":"None","facet_row":"None","nbins_col":"auto","nbins_row":"auto","title":""},"id":"ㅁ"}'

data = requests.get_json()
print(data)

