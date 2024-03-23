# Utility methods for hvplot
from pydantic import BaseModel, AnyHttpUrl
import base64
import re
from itsdangerous import TimestampSigner
import uuid
from pathlib import Path
import os
import json
import requests


pandas_frequency_offsets = {
            "Hourly": "h",
            "Calendar day": "D",
            "Weekly": "W",
            "Month end": "M",
            "Quarter end": "Q",
            "Yearly": "Y",
        }

class ModelURL(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_

    example usage:
    try:
        ModelURL(url='ftp://invalid.url')
    except ValidationError as e:
        print(e)
    """

    url: AnyHttpUrl
    
    
def generate_download_string():
    """_summary_

    Args:
        df (_type_): _description_
        filename (_type_): _description_
        title (_type_): _description_

    Returns:
        _type_: _description_

    example usage:
    generate_download_link(df, filename="download.csv", title="Download CSV file")
    """
    
    download_url = ""
    output_format = "csv"
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    unique = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    filename = str(unique) + "." + str(output_format)
    s = TimestampSigner("secret-key")
    download_token = s.sign(filename).decode()
    # dirpath = os.path.join(os.path.dirname(__file__),'static', download)
    # dirpath = os.environ["TSPLOT_DOWNLOAD"]
    # TSPLOT_DOWNLOAD = os.path.join(os.path.dirname(__file__),'static', 'download')
    dirpath = os.environ["TSPLOT_DOWNLOAD"]
    outfile = Path(dirpath, str(download_token))
    return outfile


def dict_to_html(dd, level=0):
    """
    Convert dict to html using basic html tags
    """
    text = ''
    for k, v in dd.items():
        text += '<br>' + '&nbsp;'*(4*level) + '<b>%s</b>: %s' % (k, dict_to_html(v, level+1) if isinstance(v, dict) else (json.dumps(v) if isinstance(v, list) else v))
    return text

def dict_to_html_ul(dd, level=0):
    """
    Convert dict to html using ul/li tags
    """
    text = '<ul>'
    for k, v in dd.items():
        text += '<li><b>%s</b>: %s</li>' % (k, dict_to_html_ul(v, level+1) if isinstance(v, dict) else (json.dumps(v) if isinstance(v, list) else v))
    text += '</ul>'
    return text

def get_download_link(data):
    processing_endpoint = os.environ["PROCESSING_ENDPOINT"]
    s: requests.Session = requests.Session()
    url: str = f"{processing_endpoint}/process_data"
    r = s.post(url, data=data)
    print(url, data)
    download_endpoint = f"{processing_endpoint}/results"
    download_url = f"{download_endpoint}/{r.json()['download_token']}"
    return download_url
