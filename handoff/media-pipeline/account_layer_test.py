"""Account-layer test for the Capture IV platform (user-platform-ui-redesign).

Runs the real Flask app with its test client against a throwaway copy of the
local demo database. Layers: Platform Owner, company admin, company employee,
client viewer (project code, no account), anonymous, and a second company for
tenant isolation. Nothing here touches production or any external service.
"""
import os, re, shutil, sys, tempfile, json

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
WORK = tempfile.mkdtemp(prefix='roletest-')
DB = os.path.join(WORK, 'test.db')
shutil.copy(S + '/audit.db', DB)
os.environ.update(APP_ENV='development', SECRET_KEY='role-test-only', ADMIN_USERNAME='admin',
                  ADMIN_PASSWORD=os.environ.get('LOCAL_TEST_PASSWORD', 'set-a-local-test-password'), DATABASE_URL='sqlite:///' + DB, STORAGE_BACKEND='local')
sys.path.insert(0, '/home/user/uplat'); os.chdir('/home/user/uplat')
import app as portal  # noqa: E402

A = portal.app
A.config['TESTING'] = True
PW = os.environ.get('LOCAL_TEST_PASSWORD', 'set-a-local-test-password')
results = []

def check(name, ok, detail=''):
    results.append((name, bool(ok), detail)); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

# ---------------------------------------------------------------- fixtures
with A.app_context():
    db = portal.db
    a_co = portal.Company.query.filter_by(name='Audit Co').first()
    b_co = portal.Company(name='Other Build Co', status='active', storage_limit_bytes=10**10); db.session.add(b_co); db.session.flush()
    def mk(username, admin, company, role, projects=()):
        u = portal.User(username=username, name=username, is_admin=admin, email_verified=True); u.set_password(PW)
        db.session.add(u); db.session.flush()
        db.session.add(portal.CompanyMembership(company_id=company.id, user_id=u.id, role=role, status='active'))
        for pr in projects: db.session.add(portal.ProjectAssignment(company_id=company.id, user_id=u.id, project=pr))
        return u
    mk('employee-a', False, a_co, 'employee', ['Riverside Commons'])
    admin_b = mk('admin-b', True, b_co, 'company_admin')
    b_access = portal.ProjectAccess(project='Other Site', code='QZQZ', company_id=b_co.id, allow_overview=True, allow_media=True, allow_documents=True)
    db.session.add(b_access)
    up = str(portal.UPLOAD_DIR); os.makedirs(up, exist_ok=True)
    with open(os.path.join(up, 'roletest-b-secret.pdf'), 'wb') as f: f.write(b'%PDF-1.4 company B only')
    import datetime as dt
    db.session.add(portal.ProjectFile(date=dt.date(2026, 11, 3), name='B private file', filename='roletest-b-secret.pdf', category='pdf',
                                      project='Other Site', company_id=b_co.id, uploaded_by=admin_b.id, file_size=24))
    expired = portal.ProjectAccess(project='Expired Test Project', code='XPRD', company_id=a_co.id, allow_overview=True,
                                   expires_at=portal.now_utc() - dt.timedelta(days=1))
    revoked = portal.ProjectAccess(project='Revoked Test Project', code='RVKD', company_id=a_co.id, allow_overview=True,
                                   revoked_at=portal.now_utc())
    db.session.add_all([expired, revoked]); db.session.commit()
    rv = portal.ProjectAccess.query.filter_by(code='RVCM').first(); RV_TOKEN = rv.share_token
    B_TOKEN = b_access.share_token; XP_TOKEN = expired.share_token
    a_doc = portal.ProjectFile.query.filter_by(project='Riverside Commons', company_id=a_co.id).first().filename

def csrf(c, path='/login'):
    html = c.get(path).get_data(as_text=True)
    m = re.search(r'name="_csrf" value="([^"]+)"', html); return m.group(1) if m else ''

def login(username):
    c = A.test_client()
    r = c.post('/login', data={'_csrf': csrf(c), 'username': username, 'password': PW})
    return c, r

def st(c, path): return c.get(path).status_code
def page(c, path): return c.get(path).get_data(as_text=True)

# ---------------------------------------------------------------- 1. logins
po, r = login('admin');      check('Platform Owner can sign in', r.status_code in (302, 303), r.headers.get('Location', ''))
ca, r = login('audit-admin'); check('Company admin can sign in', r.status_code in (302, 303), r.headers.get('Location', ''))
em, r = login('employee-a');  check('Company employee can sign in', r.status_code in (302, 303), r.headers.get('Location', ''))
cb, r = login('admin-b');     check('Second company admin can sign in', r.status_code in (302, 303))
bad = A.test_client(); r = bad.post('/login', data={'_csrf': csrf(bad), 'username': 'audit-admin', 'password': 'wrong'})
check('Wrong password is rejected', r.status_code == 200 and 'Sign in' in r.get_data(as_text=True) or r.status_code in (400, 401, 403))
anon = A.test_client()

# ---------------------------------------------------------------- 2. Sandbox (Platform Owner only)
check('Sandbox: Platform Owner opens it', st(po, '/admin/fieldview-sandbox') == 200)
check('Sandbox: company admin is blocked', st(ca, '/admin/fieldview-sandbox') == 403)
check('Sandbox: employee is blocked', st(em, '/admin/fieldview-sandbox') == 403)
check('Sandbox: anonymous is sent to login', st(anon, '/admin/fieldview-sandbox') in (302, 401))
check('Sandbox save: company admin is blocked',
      ca.post('/admin/fieldview-sandbox/save', data={'_csrf': csrf(ca, '/dashboard'), 'project_data': '{}'}).status_code == 403)
check('Sandbox link hidden for company admin', 'fieldview-sandbox' not in page(ca, '/dashboard'))
check('Sandbox link hidden for employee', 'fieldview-sandbox' not in page(em, '/dashboard'))

# ---------------------------------------------------------------- 3. Platform Owner console
check('Owner console: Platform Owner opens it', st(po, '/owner') == 200)
for n, c in (('company admin', ca), ('employee', em), ('second company admin', cb)):
    check(f'Owner console: {n} is blocked', st(c, '/owner') in (302, 403))
check('Owner console: anonymous is sent to login', st(anon, '/owner') in (302, 401))

# ---------------------------------------------------------------- 4. company admin vs employee
check('Company admin opens Admin', st(ca, '/admin') == 200)
check('Employee is blocked from Admin', st(em, '/admin') in (302, 403))
check('Company admin opens Upload', st(ca, '/admin/upload') == 200)
check('Employee dashboard loads', st(em, '/dashboard') == 200)
check('Employee cannot create users',
      em.post('/admin/users/create', data={'_csrf': csrf(em, '/dashboard'), 'username': 'x', 'name': 'x'}).status_code in (302, 403))
check('Employee cannot create project codes',
      em.post('/admin/projects/access', data={'_csrf': csrf(em, '/dashboard'), 'project': 'Riverside Commons'}).status_code in (302, 403))

# ---------------------------------------------------------------- 5. tenant isolation
check('Company A admin cannot fetch company B file', st(ca, '/files/roletest-b-secret.pdf') in (403, 404))
check('Company B admin can fetch its own file', st(cb, '/files/roletest-b-secret.pdf') == 200)
check('Company B admin cannot fetch company A file', st(cb, f'/files/{a_doc}') in (403, 404))
dash_a = page(ca, '/dashboard'); dash_b = page(cb, '/dashboard')
check('Company A dashboard does not list company B project', 'Other Site' not in dash_a)
check('Company B dashboard does not list company A projects', 'Riverside Commons' not in dash_b and 'Audit Plaza' not in dash_b)
api_a = ca.get('/api/projects'); check('Company A projects API excludes company B', api_a.status_code != 200 or 'Other Site' not in api_a.get_data(as_text=True))
check('Company A audit log excludes company B', 'admin-b' not in ca.get('/api/audit').get_data(as_text=True))

# ---------------------------------------------------------------- 6. client viewer (project code gate)
cl = A.test_client()
check('Client: share link without code shows code entry, not the project',
      'Flight Scans' not in page(cl, f'/share/{RV_TOKEN}') or 'code' in page(cl, f'/share/{RV_TOKEN}').lower())
check('Client: share link without code does not render the viewer', 'viewer-topnav' not in page(cl, f'/share/{RV_TOKEN}'))
r = cl.get('/project/RVCM'); check('Client: old /project/CODE URL redirects to code entry', r.status_code in (301, 302) and '/share/' in r.headers.get('Location', ''))
check('Client: old URL still needs the code', 'viewer-topnav' not in page(cl, r.headers.get('Location', '/')))
check('Client: file download blocked before code entry', st(cl, f'/files/{a_doc}') == 403)
r = cl.post(f'/share/{RV_TOKEN}', data={'_csrf': csrf(cl, f'/share/{RV_TOKEN}'), 'code': 'ABCD'})
check('Client: wrong code is rejected', 'viewer-topnav' not in r.get_data(as_text=True))
r = cl.post('/', data={'_csrf': csrf(cl, '/'), 'code': 'RVCM'})
check('Client: correct code opens the project', r.status_code in (302, 303) and RV_TOKEN in r.headers.get('Location', ''))
check('Client: viewer renders after code', 'viewer-topnav' in page(cl, f'/share/{RV_TOKEN}?tab=map'))
check('Client: can download a permitted file of this project', st(cl, f'/files/{a_doc}') == 200)
check("Client: cannot download another company's file", st(cl, '/files/roletest-b-secret.pdf') in (403, 404))
check("Client: cannot open another project's share link without its code", 'viewer-topnav' not in page(cl, f'/share/{B_TOKEN}'))
for path in ('/dashboard', '/admin', '/admin/upload', '/owner', '/admin/fieldview-sandbox'):
    check(f'Client: cannot open {path}', st(cl, path) in (302, 401, 403))
check('Client: cannot edit (create project code)',
      cl.post('/admin/projects/access', data={'_csrf': csrf(cl, '/'), 'project': 'Riverside Commons'}).status_code in (302, 401, 403))
ex = A.test_client(); r = ex.post('/', data={'_csrf': csrf(ex, '/'), 'code': 'XPRD'})
check('Client: expired code does not open the project', XP_TOKEN not in r.headers.get('Location', ''))
rk = A.test_client(); r = rk.post('/', data={'_csrf': csrf(rk, '/'), 'code': 'RVKD'})
check('Client: revoked code does not open the project', '/share/' not in r.headers.get('Location', ''))

# ---------------------------------------------------------------- 7. brute-force protection on code entry
bf = A.test_client(); codes = []
for i in range(22):
    codes.append(bf.post('/', data={'_csrf': csrf(bf, '/'), 'code': 'ZZ' + chr(65 + i // 26) + chr(65 + i % 26)}).status_code)
check('Code entry is rate-limited after 20 attempts', 429 in codes, f'first 429 at attempt {codes.index(429) + 1 if 429 in codes else "-"}')

# ---------------------------------------------------------------- 8. logout
r = ca.post('/logout', data={'_csrf': csrf(ca, '/dashboard')}); check('Logout ends the session', st(ca, '/dashboard') in (302, 401))

passed = sum(1 for _, ok, _ in results if ok)
print(f'\n{passed}/{len(results)} checks passed')
json.dump(results, open(S + '/roletest/results.json', 'w'), indent=1)
shutil.rmtree(WORK, ignore_errors=True)
try: os.remove(os.path.join(up, 'roletest-b-secret.pdf'))
except OSError: pass
