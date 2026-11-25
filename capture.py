from playwright.sync_api import sync_playwright
from pathlib import Path
B=Path(__file__).parent
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1440,'height':1550},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8501',wait_until='networkidle');page.wait_for_timeout(4000)
 page.screenshot(path=str(B/'screenshots/ternary-2022.png'),full_page=True)
 page.locator('iframe').first.screenshot(path=str(B/'screenshots/ternary-chart-2022.png'))
 page.get_by_role('tab',name='Windsock map').click();page.wait_for_timeout(2500)
 page.screenshot(path=str(B/'screenshots/windsock-2022.png'),full_page=True)
 page.locator('iframe').first.screenshot(path=str(B/'screenshots/windsock-chart-2022.png'))
 page.get_by_text('Melbourne',exact=True).click();page.wait_for_timeout(2500)
 page.locator('iframe').first.screenshot(path=str(B/'screenshots/windsock-melbourne-2022.png'))
 # Verify a historical year changes the chart and still renders.
 page.get_by_test_id('stSidebar').get_by_role('combobox').first.click();page.get_by_test_id('stSidebar').get_by_role('combobox').first.fill('1982');page.get_by_test_id('stSidebar').get_by_role('combobox').first.press('Enter');page.wait_for_timeout(2000)
 page.locator('iframe').first.screenshot(path=str(B/'screenshots/windsock-melbourne-1982.png'))
 print('Screenshots captured; browser errors:',errors)
 browser.close()
