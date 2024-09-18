import json

from fasthtml.common import Style, Link, fast_app, serve, Title, Main, Body, Header, H1, Input, Form, P, Div, Select, Option, Script, Ul, Li, A

from fh_altair import altair_headers, altair2fasthtml
from fh_matplotlib import matplotlib2fasthtml

import altair as alt
import matplotlib.pyplot as plt

import polars as pl

style = Link(rel="stylesheet", href="assets/general.css", type="text/css")
font = Style("""@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');""")
body_style = """
          padding: 0; margin: 0; box-sizing: border-box; font-size: 62.5%; 
          font-family: 'Rubik', sans-serif; line-height: 1; font-weight: 400; color: #555
          """
plot_lib = Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js")

# Start FastHTML app
app, rt = fast_app(pico=False, hdrs=(style, font, altair_headers, plot_lib))

dataset_source = r"london_weather.csv"

df = pl.read_csv(dataset_source)

def tweak_dataframe(df):
    tweaked_df = (df
          .with_columns(
            year=pl.col("date").cast(pl.String).str.to_datetime("%Y%m%d").dt.year())
          .group_by('year', maintain_order=True)
          .agg(pl.col(pl.Float64).mean())
          )
    return tweaked_df

tweaked_df = tweak_dataframe(df)

# Initialize with default values
selected_column = tweaked_df.columns[1]
selected_start_year = tweaked_df['year'].min()
selected_end_year = tweaked_df['year'].max()
cols = tweaked_df.columns[1:]

# Plotting functions
def altair_weather_plot(data, column):
   col_name = str(column).replace("_", " ").title()
   title = f'Scatter Plot of Mean {col_name} by Year'
   color="#0b2545"

   chart = alt.Chart(data, title=title).mark_point(color=color).encode(
        alt.X("year:O").title("Year"),
        alt.Y(f"{column}:Q").title(col_name),
        alt.Tooltip(f"{column}:Q", format=".2f")
        ).properties(width=400, height=200
        ).add_params(alt.selection_interval())
   
   bars = alt.Chart(data).mark_bar(color=color).encode(
        alt.Y("year:O").title("Year"),
        alt.X(f"{column}:Q").title(col_name),
        alt.Tooltip(f"{column}:Q", format=".2f")
        ).properties(width=400, height=200
        ).add_params(alt.selection_interval())
   
   return altair2fasthtml(chart & bars)


@matplotlib2fasthtml
def mpl_weather_plot(data, column):
  color = "#0b2545"
  fig, ax = plt.subplots()
  ax.scatter(data['year'], data[column], s=60, color=color)

  ax.set_xlabel('Year')
  ax.set_ylabel(f"{str(column).replace('_', ' ').title()}")
  ax.set_title(f'Scatter Plot of Mean {str(column).replace("_", " ").title()} by Year')

  # Customize the grid and ticks
  ax.grid(axis="y", linestyle="dotted", color='gray', linewidth=0.5)
  ax.tick_params(axis="both", labelsize=10, colors=color)

  # Customize the spines
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  ax.spines['bottom'].set_color(color)
  ax.spines['left'].set_color(color)


def plotly_weather_plot(data, column):
   years = data['year'].to_list()
   values = data[column].to_list()  # This should be the y-axis value
   plotly_data = [{
      "x": years,
      "y": values,
      "type": "scatter",
      "mode": "markers",
      "name": f'Scatter Plot of Mean {str(column).replace("_", " ").title()} by Year'
   }]
   
   return json.dumps(plotly_data)


@app.get("/")
def get():
   return Main(
       H1("Select report", cls="header"),
       Ul(
           Li(A("Altair", href="/altair"), cls="list-item link"),
           Li(A("Matplotlib", href="/matplotlib"), cls="list-item link"),
           Li(A("Plotly", href="/plotly"), cls="list-item link"),
           cls="list"
       ), cls="container"
   )

# Separate pages
# Altair
@app.get("/altair")
def altair():
  global selected_start_year, selected_end_year
  plot = altair_weather_plot(tweaked_df, selected_column)
  column_select = Select(*[Option(str(col).replace("_", " ").title(), value=col) for col in cols], 
                         name="column_btns", form="filter-form")

  year_start_slider = Input(type="range",
                     name="year_start_range",
                     min=tweaked_df['year'].min(),
                     max=tweaked_df['year'].max(),
                     value=selected_start_year)
  
  year_end_slider = Input(type="range",
                     name="year_end_range",
                     min=tweaked_df['year'].min(),
                     max=tweaked_df['year'].max(),
                     value=selected_end_year)
  
  return Title("London Weather Data, Altair"), Main(
    Body(
      Div(
          Div(
              Form(
                  A("Navigate Home", href="/", cls="back"),
                  P("Filters", 
                  cls="heading-tertiary"),
                  P("Select column", 
                  cls="subheading"),
                  Div(column_select),
                  P("Select Start Year", 
                  cls="subheading"),
                  Div(year_start_slider),
                  P(selected_start_year, cls="heading-tertiary", id="selected-start-year"),
                  P("Select End Year", 
                  cls="subheading"),
                  Div(year_end_slider),
                  P(selected_end_year, cls="heading-tertiary", id="selected-end-year"),
                  id="filter-form", hx_trigger="input", hx_post="/update_altair_filters", hx_target="#chart", hx_swap="innerHTML",
              cls="filter-pane"
              )
          ),
          Div(
            Header(
              H1("London Weather Data, Altair", cls="heading-secondary"),
              cls="header"
              ),
            plot,
            id="chart"
          ),
          cls="container grid--2-cols-layout"
      ),
      style=body_style
    )
  )
      

@app.post("/update_altair_filters")
def update_altair_filters(data: dict):
    global selected_column, selected_start_year

    selected_column = data["column_btns"]
    selected_start_year = int(data["year_start_range"])
    selected_end_year = int(data["year_end_range"])

    filtered_df = tweaked_df.filter(pl.col("year") >= selected_start_year).filter(pl.col("year") <= selected_end_year)
    print(data)
    # Create updated plot
    updated_plot = altair_weather_plot(filtered_df, selected_column)
    
    return Div(
              Div(
                Header(
                  H1("London Weather Data, Altair", cls="heading-secondary"),
                  cls="header"
                  ),
                updated_plot,
                id="chart"
              ),
              P(selected_start_year, cls="heading-tertiary", id="selected-start-year", hx_swap_oob="true"),
              P(selected_end_year, cls="heading-tertiary", id="selected-end-year", hx_swap_oob="true")
    )

# MPL
@app.get("/matplotlib")
def matplotlib():
  global selected_start_year
  plot = mpl_weather_plot(tweaked_df, selected_column)
  column_select = Select(*[Option(str(col).replace("_", " ").title(), value=col) for col in cols], 
                         name="column_btns", form="filter-form")

  year_start_slider = Input(type="range",
                     name="year_range",
                     min=tweaked_df['year'].min(),
                     max=tweaked_df['year'].max(),
                     value=selected_start_year)
  
  return Title("London Weather Data, Matplotlib"), Main(
    Body(

      Div(
          Div(
              Form(
                  A("Navigate Home", href="/", cls="back"),
                  P("Filters", 
                  cls="heading-tertiary"),
                  P("Select column", 
                  cls="subheading"),
                  Div(column_select),
                  P("Select Start Year", 
                  cls="subheading"),
                  Div(year_start_slider),
                  P(selected_start_year, cls="heading-tertiary", id="selected-year"),
                  id="filter-form", hx_trigger="input", hx_post="/update_mpl_filters", hx_target="#chart", hx_swap="innerHTML",
              cls="filter-pane"
              )
          ),
          Div(
            Header(
              H1("London Weather Data, Matplotlib", cls="heading-secondary"),
              cls="header"
              ),
            plot,
            id="chart"
          ),
          cls="container grid--2-cols-layout"
      ),
      style=body_style
    )
  )
      

@app.post("/update_mpl_filters")
def update_mpl_filters(data: dict):
    global selected_column, selected_start_year

    selected_column = data["column_btns"]
    selected_start_year = int(data["year_range"])

    filtered_df = tweaked_df.filter(pl.col("year") >= selected_start_year)

    # Create updated plot
    updated_plot = mpl_weather_plot(filtered_df, selected_column)
    
    return Div(
              Div(
                    Header(
                      H1("London Weather Data, Matplotlib", cls="heading-secondary"),
                      cls="header"
                      ),
                    updated_plot,
                    id="chart",
                    cls=""
                  ),
              P(selected_start_year, cls="heading-tertiary", id="selected-year", hx_swap_oob="true")
    )

# Plotly
@app.get("/plotly")
def plotly():
  global selected_start_year
  plot = plotly_weather_plot(tweaked_df, selected_column)
  column_select = Select(*[Option(str(col).replace("_", " ").title(), value=col) for col in cols], 
                         name="column_btns", form="filter-form")

  year_start_slider = Input(type="range",
                     name="year_range",
                     min=tweaked_df['year'].min(),
                     max=tweaked_df['year'].max(),
                     value=selected_start_year)
  
  return Title("London Weather Data, Plotly"), Main(
    Body(
      Div(
          Div(
              Form(
                  A("Navigate Home", href="/", cls="back"),
                  P("Filters", 
                  cls="heading-tertiary"),
                  P("Select column", 
                  cls="subheading"),
                  Div(column_select),
                  P("Select Start Year", 
                  cls="subheading"),
                  Div(year_start_slider),
                  P(selected_start_year, cls="heading-tertiary", id="selected-year"),
                  id="filter-form", hx_trigger="input", hx_post="/update_plotly_filters", hx_target="#chart", hx_swap="innerHTML",
              cls="filter-pane"
              )
          ),
          Div(
            Header(
              H1("London Weather Data, Plotly", cls="heading-secondary"),
              cls="header"
              ),
            Div(id="myDiv"),  # Chart will be rendered here
            Script(f"var data = {plot}; Plotly.newPlot('myDiv', data);"),
            id="chart"
          ),
          cls="container grid--2-cols-layout"
      ),
      style=body_style
    )
  )
      

@app.post("/update_plotly_filters")
def update_plotly_filters(data: dict):
    global selected_column, selected_start_year

    selected_column = data["column_btns"]
    selected_start_year = int(data["year_range"])

    filtered_df = tweaked_df.filter(pl.col("year") >= selected_start_year)

    # Create updated plot
    updated_plot = plotly_weather_plot(filtered_df, selected_column)
    
    return Div(
              Div(
                Header(
                  H1("London Weather Data, Plotly", cls="heading-secondary"),
                  cls="header"
                  ),
                Div(id="myDiv"),  # Chart will be rendered here
                Script(f"var data = {updated_plot}; Plotly.newPlot('myDiv', data);"),
                id="chart"
              ),
              P(selected_start_year, cls="heading-tertiary", id="selected-year", hx_swap_oob="true")
    )


serve()