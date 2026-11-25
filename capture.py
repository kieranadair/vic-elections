from pathlib import Path
import pandas as pd
import math
from playwright.sync_api import sync_playwright
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8501');args=parser.parse_args()
B=Path(__file__).parent
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(args.url,wait_until='networkidle');page.wait_for_timeout(4500)
 assert page.locator('iframe').count()==12
 assert page.get_by_text('Actual three-candidate stage',exact=True).count()==0
 print('iframe sizes',page.locator('iframe').evaluate_all('(els)=>els.map(e=>({w:e.clientWidth,h:e.clientHeight}))'))
 page.screenshot(path=str(B/'screenshots/ternary-grid-laptop.png'))
 page.locator('iframe').nth(10).screenshot(path=str(B/'screenshots/ternary-2018-static.png'))
 page.locator('iframe').nth(11).screenshot(path=str(B/'screenshots/ternary-2022-static.png'))
 frame=page.locator('iframe').nth(11)
 frame.scroll_into_view_if_needed()
 page.wait_for_timeout(250)
 frame.screenshot(path=str(B/'screenshots/ternary-winners-2022.png'))
 seat=pd.read_csv(B/'data/first_preferences.csv').query('election_year==2022 and electorate=="Northcote"').iloc[0]
 box=frame.bounding_box();h=math.sqrt(3)/2;side=min(box['width']-70,(box['height']-120)/h)
 x=(box['width']-side)/2+side*(seat.coalition_pct+seat.other_pct/2)/100
 y=72+side*h*(1-seat.other_pct/100)
 page.mouse.move(box['x']+x,box['y']+y);page.wait_for_timeout(500)
 frame.screenshot(path=str(B/'screenshots/ternary-hover-northcote-2022.png'))
 page.get_by_role('tab',name='Windsock map',exact=True).click();page.wait_for_timeout(2500)
 assert page.locator('iframe').count()==1
 page.get_by_role('tab',name='Ternary',exact=True).click();page.wait_for_timeout(2000)
 assert page.locator('iframe').count()==12
 page.set_viewport_size({'width':1366,'height':900});page.wait_for_timeout(1500)
 page.locator('section.main').count()
 page.screenshot(path=str(B/'screenshots/ternary-grid-1366.png'))
 print('browser errors',errors);assert not errors
 b.close()
