import time
import pandas as pd
import hvplot.xarray
import xarray as xr
import panel as pn
import numpy as np
import param
import functools

import holoviews as hv

from utility import ModelURL, pandas_frequency_offsets, generate_download_string, dict_to_html, dict_to_html_ul
import traceback
from pydantic import ValidationError
from starlette.templating import Jinja2Templates


from bokeh.models import Select, Button, Div, Slider
from bokeh.layouts import layout, column, row, Spacer


# from bokeh.models.widgets import (
#     DataTable,
#     TableColumn,
# )
# from bokeh.models import ColumnDataSource

pn.param.ParamMethod.loading_indicator = True


# try:
#     # phase = int(pn.state.session_args.get('phase')[0])
#     nc_url = str(pn.state.session_args.get('nc_url')[0].decode("utf8"))
# except Exception:
#     # phase = 1
#     nc_url = 'https://thredds.met.no/thredds/dodsC/alertness/YOPP_supersite/obs/utqiagvik/utqiagvik_obs_timeSeriesProfile_20180701_20180930.nc'



try:
    nc_url = str(pn.state.session_args.get('url')[0].decode("utf8"))
    try:
        ModelURL(url=nc_url)
        valid_url = True
    except ValidationError as e:
        print(e)
        valid_url = False
except TypeError:
    nc_url = None
    valid_url = False

error_log = Div(text=f"""<br><br> Can't load dataset from {nc_url} """)
templates = Jinja2Templates(directory="/app/templates")

def show_hide_error(event):
    """docstring"""
    if error_log.visible:
        error_log.visible = False
    else:
        error_log.visible = True


print("++++++++++++++++++++++++ LOADING ++++++++++++++++++++++++++++++++++++")
print(str(nc_url))
print("++++++++++++++++++++++++ +++++++ ++++++++++++++++++++++++++++++++++++")



# TODO: add a logger and tell the user that the file is being loaded
#       and if the decoding of the time variable fails
#       keep track of the nc_url and the error message

try:
    ds = xr.open_dataset(str(nc_url).strip())
except ValueError as e:
    print(e)
    ds = xr.open_dataset(str(nc_url).strip(), decode_times=False)
except OSError as e:
    raw_data = Div(text=f"""<b>ValueError</b><br><br> Can't load dataset from {nc_url} """)
    newhtml = templates.get_template("error.html").render(
        {"error_traceback": traceback.format_exc()}
    )
    error_log.text = newhtml
    error_log.visible = False
    error_log_button = Button(
        label="",
        height=50,
        width=50,
    )  # , width_policy='fixed'
    error_log_button.on_click(show_hide_error)

    print(newhtml)
    bokeh_pane = pn.pane.Bokeh(
        column(raw_data, error_log_button, error_log),
    ).servable()


# Build a list of coordinates, give precedence to time coordinates
# if no time coordinates are found use the available coordinates

# the code below could go into a method, if time is detected as a coordinate
# then the frequency selector should be added to the sidebar
# if time is not detected as a coordinate then the frequency selector should not be added to the sidebar

time_coord = [i for i in ds.coords if ds.coords.dtypes[i] == np.dtype('<M8[ns]')]

# if time is detected as a coordinate then the frequency selector should be added to the sidebar
# but I also need to check if the time coordinate is a dimension for the selectred variable
# and if the time values are sorted with monotonically increasing or decreasing values

# check for monotobically increasing or decreasing time values:
#
# coords_values = ds.coords['time'].values[::-1]
# is_monotonic = all(coords_values[i] <= coords_values[i + 1] for i in range(len(coords_values) - 1)) or all(coords_values[i] >= coords_values[i + 1] for i in range(len(coords_values) - 1))
# print("is_monotonic: ", is_monotonic)
# check if a selected variable has time as a index
# is_time_indexed = 'time' in ds['variable'].indexes
# print("variable {} is indexed by time: ", is_time_indexed)

if len(time_coord) != 0:
    frequency_selector = pn.widgets.Select(options=[
        "--",
        "Hourly",
        "Calendar day",
        "Weekly",
        "Month end",
        "Quarter end",
        "Yearly",
    ], name='Resampling Frequency')
else:
    frequency_selector = None

if len(time_coord) == 0:
    time_coord = [i for i in ds.coords]

# build a dictionary of variables and their long names
mapping_var_names = {}
for i in ds:
    if int(len(list(ds[i].coords)) != 0):
        try:
            title = f"{ds[i].attrs['long_name']} [{i}]"
        except KeyError:
            title = f"{i}"
        mapping_var_names[i] = title
        
# add a select widget for variables, uses long names
variables_selector = pn.widgets.Select(options=list(mapping_var_names.values()), name='Data Variable')

# main plotting function
def plot(var, title=None, plot_type='line'):
    time_coord = [i for i in ds.coords if ds.coords.dtypes[i] == np.dtype('<M8[ns]')]
    if len(time_coord) == 0:
        time_coord = [i for i in ds.coords]
    if not title:
        try:
            title = f"{ds[var].attrs['long_name']}"
        except KeyError:
            title = f"{var}"
    else:
        title=title
    if time_coord[0] in ds[var].coords:
        if frequency_selector is not None and frequency_selector.value != "--":
            print(f"user request to plot resampled dataset - using time dimension: {time_coord[0]}")
            print(f"available dimensions are: {time_coord}")
            arguments = {time_coord[0]: pandas_frequency_offsets[frequency_selector.value]}
            if plot_type == 'line':
                plot_widget =  ds[var].resample(**arguments).mean().hvplot.line(x=time_coord[0], grid=True, title=title, widget_location='bottom', responsive=True)
            else:
                plot_widget =  ds[var].resample(**arguments).mean().hvplot.scatter(x=time_coord[0], grid=True, title=title, widget_location='bottom', responsive=True)   
        else:
            if plot_type == 'line':
                plot_widget =  ds[var].hvplot.line(x=time_coord[0], grid=True, title=title, widget_location='bottom', responsive=True)
            else:
                plot_widget =  ds[var].hvplot.scatter(x=time_coord[0], grid=True, title=title, widget_location='bottom', responsive=True)
        # scatter_plot_widget = ds[var].hvplot.scatter(x=time_coord[0], grid=True, title=title, widget_location='bottom', responsive=True)
        #plot_widget = hv.Overlay(line_plot_widget, scatter_plot_widget)
        return plot_widget
    else:
        if plot_type == 'line':
            plot_widget =  ds[var].hvplot.line(x=list(ds[var].coords)[0], grid=True, title=title, widget_location='bottom', responsive=True)
        else:
            plot_widget =  ds[var].hvplot.scatter(x=list(ds[var].coords)[0], grid=True, title=title, widget_location='bottom', responsive=True)
        # scatter_plot_widget = ds[var].hvplot.scatter(x=list(ds[var].coords)[0], grid=True, title=title, widget_location='bottom', responsive=True)
        #plot_widget = hv.Overlay(line_plot_widget, scatter_plot_widget)
        return plot_widget

# method to update the plot when a new variable is selected    
def on_var_select(event):
    var = event.obj.value
    result = [key for key, value in mapping_var_names.items() if value == var]
    with pn.param.set_values(main_app, loading=True):
        plot_widget[-1] = plot(var=result, title=var)
        print(f'selected {result}')

def on_frequency_select(event):
    frequency = event.obj.value
    var = variables_selector.value
    result = [key for key, value in mapping_var_names.items() if value == var]
    with pn.param.set_values(main_app, loading=True):
        plot_widget[-1] = plot(var=result, title=var)
        print(f'selected {result} \n with frequency {frequency}') 
    
if frequency_selector is not None:
    frequency_selector.param.watch(on_frequency_select, parameter_names=['value'])
 
def show_hide_export_widget(event):
    print(downloader.visible)
    if downloader.visible:
        downloader.visible = False
    else:
        metadata_layout.visible = False
        downloader.visible = True 

        
def show_hide_metadata_widget(event):
    """docstring"""
    if metadata_layout.visible:
        metadata_layout.visible = False
    else:
        metadata_layout.visible = True
        downloader.visible = False
        
def export_selection(event):
    """docstring"""
    # print(box.values)
    # start = ds.index.searchsorted(date_range_slider.value[0])
    # end = ds.index.searchsorted(date_range_slider.value[1])
    # event_log.text = f"{str(wbx.value)} <br> {str(date_range_slider.value)}"
    with pn.param.set_values(main_app, loading=True):
        export_format = select_output_format.value
        if export_resampling.value == 'Raw':
            resampler = 'Raw Data'
            #print(export_resampling)
            #print(export_resampling.value)
        else:
            if frequency_selector is not None and frequency_selector.value != "--":
                resampler = frequency_selector.value
                #print(export_resampling)
                #print(export_resampling.value)
            else:
                resampler = 'Raw Data'
        if not frequency_selector:
            time_range = "Time not decoded"
        else:
            time_range = str(date_range_slider.value)
            selected_variables = [i.name for i in wbx if i.value == True]
        # event_log.text = f"{str(selected_variables)} <br> {time_range} <br> {export_format} <br> {resampler}"
        some_text = generate_download_string()
        print(some_text)
        export_dataspec = {
            'nc_url': nc_url,
            'selected_variables': selected_variables,
            'time_range': time_range,
            'export_format': export_format,
            'resampler': resampler,     
        }
        # event_log.text = f"{str(export_dataspec)}"
        event_log.text = str(
            f'<marquee behavior="scroll" direction="left"><b>. . .  processing . . .</b></marquee>'
        )
        pn.state.curdoc.add_next_tick_callback(
            functools.partial(
                compress_selection, json_data=export_dataspec, output_log_widget=event_log))
        # slice the ds by selecting the variables fro the checkbox and slicing along the time dimension from the timerange slider (if available)
    
def compress_selection(json_data, output_log_widget):
    time.sleep(10)
    output_log_widget.text = str(
                f'<a href="{json_data}">Download</a>'
            )
    
    
def build_metadata_widget():
    # dataset_metadata_keys = list(ds.attrs.keys())
    # dataset_metadata_values = list(ds.attrs.values())
    # dataset_metadata = dict(
    #     key=dataset_metadata_keys,
    #     value=dataset_metadata_values,
    # )
    # dataset_metadata_source = ColumnDataSource(dataset_metadata)

    # dataset_metadata_columns = [
    #     TableColumn(field="key", title="key"),
    #     TableColumn(field="value", title="value"),
    # ]
    # metadata_table = DataTable(
    #     source=dataset_metadata_source,
    #     columns=dataset_metadata_columns,
    # )
    metadata_text = dict_to_html_ul(ds.attrs)
    # metadata_layout = row(
    #     Spacer(width=30),
    #     column(
    #         Div(text=f'<font size = "2" color = "darkslategray" ><b>Metadata<b></font> {metadata_text}'),
    #         Spacer(height=10),
    #         #metadata_table,
    #         sizing_mode="stretch_both",
    #     ),
    # )
    # metadata_layout = Div(text=f'<font size = "2" color = "darkslategray" ><b>Metadata<b></font> {metadata_text}')
    
    
    
    metadata_layout = pn.Row(Spacer(width=10), pn.Column(Spacer(height=120),
                                                Div(text=f'<font size = "2" color = "darkslategray" ><b>Metadata<b></font> {metadata_text}'), 
                                                width=400, sizing_mode='fixed'))
    
    
    metadata_layout.visible = False

    metadata_button = Button(
        label="Metadata",
        height=30,
        width=120,
    )  # , width_policy='fixed'
    metadata_button.on_click(show_hide_metadata_widget)
    return metadata_layout, metadata_button
    
    
def build_download_widget():
    export_resampling_option = pn.widgets.RadioButtonGroup(name='Resamplig', 
                                              options=['Raw', 'Resampled'])    
    event_log = Div(text=f"""<br><br> some_log """)
    try:
        time_dim = time_coord[0]
        date_range_slider = pn.widgets.DateRangeSlider(
            name='Date Range',
            start=ds.coords[time_dim].values.min(), end=ds.coords[time_dim].values.max(),
            value=(ds.coords[time_dim].values.min(), ds.coords[time_dim].values.max()),
            step=1
        )
    except:
        date_range_slider = Div(text=f"""<br><br> Time Dimension not available """)
    
    checkbox_group = pn.FlexBox(*[pn.widgets.Checkbox(name=str(i)) for i in mapping_var_names.keys()])
    select_output_format = pn.widgets.Select(name='Export Format', options=['NetCDF', 'CSV', 'Parquet'])
    
    export_button = Button(
        label="Export",
        height=30,
        width=120,
    )  
    export_button.on_click(show_hide_export_widget)
    
    export_options_button = Button(
        label="Download",
        height=30,
        width_policy='fit'
        # width=30,
    )  # , width_policy='fixed'
    export_options_button.on_click(export_selection)
    if not frequency_selector: 
        export_resampling_option.visible = False
    
    return export_button, checkbox_group, date_range_slider, export_options_button, event_log, select_output_format, export_resampling_option




# Export Widgets
export_button, wbx, date_range_slider, export_options_button, event_log, select_output_format, export_resampling = build_download_widget()
download_header = Div(text='<font size = "2" color = "darkslategray" ><b>Data Export<b></font> <br> Variable Selection')
# download_header.visible = False


# Metadata Widgets
metadata_layout, metadata_button = build_metadata_widget()


# downloader = pn.Column(download_header, wbx, date_range_slider, select_output_format, export_resampling, export_options_button, event_log, width=400, sizing_mode='fixed')



downloader = pn.Row(Spacer(width=10), pn.Column(Spacer(height=120),
                                                download_header, 
                                                wbx, 
                                                date_range_slider, 
                                                select_output_format, 
                                                export_resampling, 
                                                export_options_button, 
                                                event_log, width=400, sizing_mode='fixed'))

downloader.visible = False

variables_selector.param.watch(on_var_select, parameter_names=['value'])

selected_var = [key for key, value in mapping_var_names.items() if value == variables_selector.value]


buttons = pn.Column(export_button, metadata_button)
plot_widget = pn.Column(pn.Row(variables_selector, frequency_selector, buttons), plot(selected_var, title=variables_selector.value))

main_app = pn.Row(plot_widget, Spacer(width=10), downloader, metadata_layout).servable()


