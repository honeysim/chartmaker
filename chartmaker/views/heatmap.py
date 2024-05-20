from flask import Flask, render_template, request, jsonify, Blueprint, session
from chartmaker.models import UserData
from chartmaker import db
from io import StringIO
from urllib.parse import parse_qs


from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import uuid

blue_heatmap = Blueprint('heatmap', __name__, url_prefix='/heatmap')

@blue_heatmap.route('/')
def index():
   if 'user_id' not in session:
   # 세션에 사용자 식별자가 없으면 생성
      session["user_id"] = str(uuid.uuid4())
   return render_template("heatmap.html")

@blue_heatmap.route('/process_data', methods=['POST'])
def process_data():
   try :
      data = request.form['data']
      user_id = session["user_id"]

      data_list = [line.split('\t') for line in data.split('\n') if line]
      columns = data_list[0]

      for idx in range(0,len(columns)):
         if columns[idx].strip() =="":
            columns[idx] = "col_"+ str(idx+1)

      df = pd.DataFrame(data_list[1:], columns=columns)

      if df.shape[0] >= 3001 :
         raise ValueError("Please input under 3000 rows.")
      
      if len(columns) != len(set(columns)):
         raise ValueError("your table has duplicated columns")      
         
      for column in df.columns:
         df[column] = pd.to_numeric(df[column], errors='ignore')
      
      df_json = df.to_json()
      
      user_data = UserData(id=str(uuid.uuid4()), user_id=user_id, df_data=df_json)
      db.session.add(user_data)
      db.session.commit()


      table = df.to_html(classes="result-table", index=False)
      table = f"""
      <div id="table-wrapper">{table}</div>
      <div class="btn-wrapper">
      <button type="button" id="show-correlation__btn">Show Correlation</button>
      <button id="reset-btn">reset</button>
      </div>
      """

      options = "".join([f"<option>{column}</option>" for column in df.columns])
      None_options = "<option>None</option>" + options
      Agg_options = "<option>count</option><option>avg</option><option>min</option><option>max</option><option>sum</option>"

      return jsonify({"Result": "success",
                      "table": table, 
                     "options": options, 
                     "NoneOptions": None_options,
                     "AggOptions" : Agg_options
                     })
   except ValueError as e:
      error_msg = str(e)
      return jsonify({"Result": "error", "ErrorMsg": error_msg})
   
   except:
      error_msg = """Each column should have the same length\nFirst row must be table's column"""
      return jsonify({"Result": "error", "ErrorMsg": error_msg})

@blue_heatmap.route('/draw_chart', methods=['POST'])
def draw_chart():
   try:
   # 데이터베이스에서 사용자 데이터 불러오기
      user_id = session["user_id"]
      user_data = UserData.query.filter_by(user_id=user_id).order_by(UserData.created_at.desc()).first()
      df_data = user_data.df_data
      df = pd.read_json(StringIO(df_data))

      data = request.get_json()
      id = data["id"]
      print(id)
         
      if id=="corr":
         fig = px.imshow(df.corr(numeric_only=True),
                         title="correlation heatmap")
         fig.update_layout(title_x=0.5, margin=dict(t=60))
         chart_json = fig.to_json()
         return jsonify({"Result": "success", "ChartJson": chart_json})
      else:
         variables = request.get_json().get("variables")

         if "x_datetime" in variables :
            df[variables["x_axis"]] = pd.to_datetime(df[variables["x_axis"]])
         
         elif "y_datetime" in variables :
            df[variables["y_axis"]] = pd.to_datetime(df[variables["y_axis"]])

         # Plotly를 사용하여 차트 생성
         fig = px.density_heatmap(data_frame=df, 
                           x=variables["x_axis"], 
                           y=variables["y_axis"],
                           z = None if variables["value"] == "None" else variables["value"],
                           histfunc=None if variables["agg"] == "None" else variables["agg"],
                           facet_col = None if variables["facet_col"] == "None" else variables["facet_col"],
                           facet_row = None if variables["facet_row"] == "None" else variables["facet_row"],
                           nbinsx = None if variables["nbins_col"] == "auto" else int(variables["nbins_col"]),
                           nbinsy= None if variables["nbins_row"] == "auto" else int(variables["nbins_row"]),
                           template="ggplot2",
                           title= variables["title"])

         fig.update_layout(title_x=0.5,
                           margin=dict(t=60))
         
         chart_json = fig.to_json()
         return jsonify({"Result": "success", "ChartJson": chart_json})
   
   except:
      error_msg = "check your variables"
      return jsonify({"Result": "error", "ErrorMsg": error_msg})    
