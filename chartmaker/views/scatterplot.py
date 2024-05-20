from flask import Flask, render_template, request, jsonify, Blueprint, session
from chartmaker.models import UserData
from chartmaker import db
from io import StringIO

from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import uuid

blue_scatter = Blueprint('scatterplot', __name__, url_prefix='/scatterplot')

@blue_scatter.route('/')
def index():
   if 'user_id' not in session:
   # 세션에 사용자 식별자가 없으면 생성
      session["user_id"] = str(uuid.uuid4())
   return render_template("scatterplot.html")

@blue_scatter.route('/process_data', methods=['POST'])
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

      return jsonify({"Result": "success",
                      "table": table, 
                     "options": options, 
                     "NoneOptions": None_options,
                     })
   except ValueError as e:
      error_msg = str(e)
      return jsonify({"Result": "error", "ErrorMsg": error_msg})
   
   except:
      error_msg = """Each column should have the same length\nFirst row must be table's column"""
      return jsonify({"Result": "error", "ErrorMsg": error_msg})



      
                   
@blue_scatter.route('/draw_chart', methods=['POST'])
def draw_chart():
   try: 
      # 데이터베이스에서 사용자 데이터 불러오기
      user_id = session["user_id"]
      user_data = UserData.query.filter_by(user_id=user_id).order_by(UserData.created_at.desc()).first()
      df_data = user_data.df_data
      df = pd.read_json(StringIO(df_data))
      
      id = request.get_json().get("id")
      if id=="corr":
         fig = px.imshow(df.corr(numeric_only=True),
                         title="correlation heatmap",
                         color_continuous_scale=px.colors.sequential.Blues)
         fig.update_layout(title_x=0.5, margin=dict(t=60))
         chart_json = fig.to_json()
         return jsonify({"Result": "success", "ChartJson": chart_json})
      
      else:
         variables = request.get_json().get("variables")

         # Plotly를 사용하여 차트 생성
         template_dict = {"White":"plotly_white", "Simple-White":"simple_white", 
                        "Dark": "plotly_dark", "Gray":"ggplot2", 
                        "Seaborn":"seaborn", "Presentation":"presentation"}

         fig = px.scatter(df, x=variables["x_axis"], 
                           y=variables["y_axis"],
                           color = None if variables["color"] == "None" else variables["color"],
                           facet_col = None if variables["facet_col"] == "None" else variables["facet_col"],
                           facet_row = None if variables["facet_row"] == "None" else variables["facet_row"],
                           size = None if variables["size"] == "None" else variables["size"],
                           template = None if variables["style"] == "Default" else template_dict[variables["style"]],
                           symbol = None if variables["symbol"] == "None" else variables["symbol"],
                           title= variables["title"])
               
         fig.update_layout(title_x=0.5, margin=dict(t=60))

         chart_json = fig.to_json()
         return jsonify({"Result": "success", "ChartJson": chart_json})  
      
   except:      
      error_msg = "type error"
      return jsonify({"Result": "error", "ErrorMsg": error_msg}) 

