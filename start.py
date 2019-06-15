import ipywidgets as ipw

def get_start_widget(appbase, jupbase):
    #http://fontawesome.io/icons/
    template = """
    <table>
    <tr>
        <th style="text-align:center">Phonon Calculations</th>
        <th style="width:60px" rowspan=2></th>
        
    <tr>
    <td valign="top"><ul>
        <li><a href="{appbase}/submit_phonons.ipynb" target="_blank">Submit</a>
    </ul></td>
    

    </tr></table>

"""
    
    html = template.format(appbase=appbase, jupbase=jupbase)
    return ipw.HTML(html)
    
#EOF
