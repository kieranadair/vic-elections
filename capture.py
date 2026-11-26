"""Visual checks for the three-chart story rows; run against a local preview."""
from pathlib import Path
import argparse
import math
import pandas as pd
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:8501')
args = parser.parse_args()
ROOT = Path(__file__).parent

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.url, wait_until='networkidle')
    page.wait_for_timeout(3000)
    assert page.locator('iframe').count() == 12
    assert page.get_by_role('tab').count() == 0
    assert page.get_by_text('Windsock map', exact=True).count() == 0
    for width in [1440, 1366]:
        page.set_viewport_size({'width': width, 'height': 1000})
        page.wait_for_timeout(1000)
        page.get_by_role('heading',level=1).scroll_into_view_if_needed()
        boxes = [frame.bounding_box() for frame in page.locator('iframe').all()]
        for index in [0, 3, 6, 9]:
            assert max(box['y'] for box in boxes[index:index+3]) - min(box['y'] for box in boxes[index:index+3]) < 2
        assert page.evaluate('getComputedStyle(document.body).backgroundColor') == 'rgb(255, 255, 255)'
        assert min(box['width'] for box in boxes) >= 295, 'Triangles must not shrink at laptop widths'
        page.get_by_role('heading',level=1).evaluate("el => {for(let p=el;p;p=p.parentElement){p.scrollTop=0;}window.scrollTo(0,0);}")
        page.wait_for_timeout(200)
        page.screenshot(path=str(ROOT / 'screenshots' / f'story-{width}.png'))
    for row in range(4):
        first = page.locator('iframe').nth(row*3)
        first.scroll_into_view_if_needed()
        page.wait_for_timeout(350)
        heading=page.get_by_role('heading',level=3).nth(row)
        assert heading.bounding_box()['x'] < first.bounding_box()['x']
        section=heading.locator('xpath=ancestor::div[@data-testid="stHorizontalBlock"][1]')
        section.screenshot(path=str(ROOT / 'screenshots' / f'story-period-{row+1}.png'))
    frame = page.locator('iframe').nth(11)
    frame.screenshot(path=str(ROOT / 'screenshots' / 'ternary-2022-story.png'))
    frame.scroll_into_view_if_needed()
    seat = pd.read_csv(ROOT/'data/first_preferences.csv').query('election_year==2022 and electorate=="Northcote"').iloc[0]
    box = frame.bounding_box()
    h = math.sqrt(3)/2
    side = min(box['width']-48, (box['height']-164)/h)
    x = (box['width']-side)/2 + side*(seat.coalition_pct+seat.other_pct/2)/100
    y = 74 + side*h*(1-seat.other_pct/100)
    page.mouse.move(box['x']+x, box['y']+y)
    page.wait_for_timeout(400)
    frame.screenshot(path=str(ROOT/'screenshots/ternary-hover-story.png'))
    page.get_by_role('heading',name='Explore Your Electorate',exact=True).scroll_into_view_if_needed()
    page.get_by_role('heading',name='Explore Your Electorate',exact=True).evaluate("el=>el.scrollIntoView({block:'start'})")
    assert page.get_by_role('combobox').bounding_box()['y'] < page.get_by_text('The statewide story brings together many local contests.',exact=False).bounding_box()['y']
    page.wait_for_timeout(500)
    page.screenshot(path=str(ROOT/'screenshots/explore-statewide.png'))
    # A selected seat keeps its guides after the pointer leaves the chart.
    selector=page.get_by_role('combobox')
    selector.click()
    selector.fill('Northcote')
    page.get_by_role('option',name='Northcote',exact=True).click()
    page.wait_for_timeout(1300)
    print('Selected input:',selector.input_value(),'selectbox text:',page.get_by_test_id('stSelectbox').inner_text())
    assert selector.input_value()=='Northcote' or 'Northcote' in page.get_by_test_id('stSelectbox').inner_text()
    page.get_by_role('heading',name='Explore Your Electorate',exact=True).evaluate("el=>el.scrollIntoView({block:'start'})")
    page.screenshot(path=str(ROOT/'screenshots/explore-northcote.png'))
    canvas=page.get_by_test_id('stEChartsChart').locator('canvas').first
    trend_box=canvas.bounding_box()
    page.mouse.move(trend_box['x']+trend_box['width']-166,trend_box['y']+20+(trend_box['height']-64)*(1-seat.labor_pct/100))
    page.wait_for_timeout(400)
    assert page.get_by_text('Elected: Labor',exact=False).is_visible()
    assert page.get_by_text('Labor: 41%',exact=False).is_visible()
    page.screenshot(path=str(ROOT/'screenshots/explore-northcote-hover.png'))
    page.mouse.move(5,5)
    page.locator('iframe').nth(11).screenshot(path=str(ROOT/'screenshots/electorate-highlight-2022.png'))
    page.get_by_role('heading',level=1).scroll_into_view_if_needed()
    page.get_by_text('Reading the charts',exact=True).click()
    page.wait_for_timeout(1400)
    assert page.locator('iframe').count()==13
    assert page.get_by_text('Dummy data:',exact=False).count()==2
    example=page.get_by_test_id('stExpander').locator('iframe')
    example.screenshot(path=str(ROOT/'screenshots/ternary-explainer-example.png'))
    page.screenshot(path=str(ROOT/'screenshots/chart-guide.png'))
    page.get_by_test_id('stExpander').screenshot(path=str(ROOT/'screenshots/chart-guide.png'))
    page.get_by_text('Reading the charts',exact=True).click()
    page.wait_for_timeout(600)
    # The gallery also wraps without horizontal overflow on phones.
    page.set_viewport_size({'width':390,'height':844})
    page.wait_for_timeout(500)
    assert page.locator('iframe').first.bounding_box()['width'] < 390
    assert not errors, errors
    print('Three charts per row and four rows at laptop widths; context on the left; chart sizes preserved; hover and mobile wrap pass.')
    browser.close()
