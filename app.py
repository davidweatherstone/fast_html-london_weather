from fasthtml.common import Style, Link, fast_app, serve, Title, Main, Body, Header, H1, Input, Form, P, Div, Select, Option
from fh_matplotlib import matplotlib2fasthtml
import matplotlib.pyplot as plt
import polars as pl

style = Link(rel="stylesheet", href="assets/general.css", type="text/css")
font = Style("""@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap');""")
body_style = """
          padding: 0; margin: 0; box-sizing: border-box; font-size: 62.5%; 
          font-family: 'Rubik', sans-serif; line-height: 1; font-weight: 400; color: #555
          """

# Start FastHTML app
app, rt = fast_app(pico=False, hdrs=(style, font))

dataset_source = r"london_weather.csv"

df = pl.read_csv(dataset_source)

tweaked_df = (df
.with_columns(
  year=pl.col("date").cast(pl.String).str.to_datetime("%Y%m%d").dt.year())
.group_by('year', maintain_order=True)
.agg(pl.col(pl.Float64).mean())
)

cols = tweaked_df.columns[1:]

# Initialize with default values
selected_column = tweaked_df.columns[1]
selected_year = tweaked_df['year'].min()

@matplotlib2fasthtml
def weather_plot(data, column):
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


@app.get("/")
def get():
  global selected_year
  plot = weather_plot(tweaked_df, selected_column)
  column_select = Select(*[Option(str(col).replace("_", " ").title(), value=col) for col in cols], 
                         name="column_btns", form="filter-form")

  year_slider = Input(type="range",
                     name="year_range",
                     min=tweaked_df['year'].min(),
                     max=tweaked_df['year'].max(),
                     value=selected_year)
  
  return Title("London Weather Data"), Main(
    Body(

      Div(
          Div(
              Form(
                  P("Filters", 
                  cls="heading-tertiary"),
                  P("Select column", 
                  cls="subheading"),
                  Div(column_select),
                  P("Select Start Year", 
                  cls="subheading"),
                  Div(year_slider),
                  P(selected_year, cls="heading-tertiary", id="selected-year"),
                  id="filter-form", hx_trigger="input", hx_post="/update_filters", hx_target="#chart", hx_swap="innerHTML",
              cls="filter-pane"
              )
          ),
          Div(
            Header(
              H1("London Weather Data", cls="heading-secondary"),
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
      

@app.post("/update_filters")
def update_filters(data: dict):
    global selected_column, selected_year

    selected_column = data["column_btns"]
    selected_year = int(data["year_range"])

    filtered_df = tweaked_df.filter(pl.col("year") >= selected_year)

    # Create updated plot
    updated_plot = weather_plot(filtered_df, selected_column)
    
    return Div(
              Div(
                    Header(
                      H1("London Weather Data", cls="heading-secondary"),
                      cls="header"
                      ),
                    updated_plot,
                    id="chart",
                    cls=""
                  ),
              P(selected_year, cls="heading-tertiary", id="selected-year", hx_swap_oob="true")
    )


serve()
