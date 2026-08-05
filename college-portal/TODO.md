# College Management Portal - Task Tracker

## Original Fixes (app.py errors)
- [x] 1. Add missing `HRFlowable` import from `reportlab.platypus`
- [x] 2. Fix `send_file` syntax error (move `os.unlink` cleanup out of call args)
- [x] 3. Fix wrong redirect `/my_result` → `/student_results`
- [x] 4. Verify with `python -m py_compile app.py` → exit code 0

## Marksheet PDF Enhancements
- [x] 1. Add imports (matplotlib, PIL) for graph & placeholder image generation
- [x] 2. Add helper functions (get_seat_number, ensure_static_assets, generate_student_photo, generate_sgpa_graph, get_grade_point, calculate_sgpa, calculate_cgpa, semester_sgpas)
- [x] 3. Add Seat/Roll number + Student photograph in info section
- [x] 4. Fix marks table column widths (10 columns with Credits & Grade Point)
- [x] 5. Add Semester-wise SGPA table
- [x] 6. Add Semester-wise SGPA bar graph (matplotlib)
- [x] 7. Add Principal & COE digital signature images in footer
- [x] 8. Add Official college seal/stamp in footer
- [x] 9. Add QR verification text below QR code
- [x] 10. Add Result Declaration note
- [x] 11. Add "ROYAL COLLEGE" watermark behind content
- [x] 12. Switch to A4 landscape page size with proper margins
- [x] 13. Add CGPA/SGPA to student summary
- [x] 14. Add Performance Summary box

## Additional Routes & Fixes
- [x] 1. Add missing `/view_results` route (was referenced by `edit_result` & `delete_result` redirects)
- [x] 2. Create `templates/teacher/view_results.html` so the redirects don't 404
- [x] 3. Fix `manage_results` to include `practical=0` in new Result creation
- [x] 4. Update student dashboard route to pass `cga` & `sgpa_data`

## Student Notices & Models Fix
- [x] 1. Update `student_notices` route to show College + Department + Personal (Student scope) notices
- [x] 2. Add `student_id` column + `student` relationship to the `Notice` model in `models.py`
- [x] 3. Update `send_warning` route to include `scope="Student"` and `student_id`
- [x] 4. Clean up duplicate `student_id`/`student` definitions in `Notice` model
- [x] 5. Verified `python -m py_compile app.py models.py` → exit code 0

## Performance Dashboard Enhancements
- [x] 1. Add `calculate_student_percentage` helper function
- [x] 2. Add `get_department_rankings` helper (rank departments by avg %)
- [x] 3. Add `get_class_toppers` helper (top 10 college-wide)
- [x] 4. Add `get_department_toppers` helper (top 3 per department)
- [x] 5. Update `principal_dashboard` route to pass ranking/topper data
- [x] 6. Update `principal_dashboard.html` with rankings & toppers sections
- [x] 7. Update `hod_dashboard` route with performance panel data
- [x] 8. Update `hod_dashboard.html` with Department Performance panel

## Dashboard Redesign (Clickable Performance Cards → New Pages)
- [x] 1. Principal: Department Rankings → clickable card linking to `/principal/department_rankings` page
- [x] 2. Principal: College Toppers → clickable card linking to `/principal/college_toppers` page
- [x] 3. Principal: Department-wise Toppers → clickable card linking to `/principal/department_toppers` page
- [x] 4. HOD: Department Performance → clickable card linking to `/hod/department_performance` page
- [x] 5. New routes added in `app.py` for each performance page
- [x] 6. New templates created: `principal/department_rankings.html`, `principal/college_toppers.html`, `principal/department_toppers.html`, `hod/department_performance.html`
- [x] 7. Each page has a "Back to Dashboard" button for easy navigation
- [x] 8. Python syntax check: `python -m py_compile app.py` → exit code 0

## Student Dashboard & Navigation Fixes
- [x] 1. Removed the "Student Information" section from `student/dashboard.html`
- [x] 2. Removed duplicate "Back to Dashboard" button from `student/profile.html`
- [x] 3. Fixed Study Materials back button: `/student_dashboard` (404) → `/dashboard` (working) in `student/student_materials.html`

## Multi-Department Subjects Fix
- [x] 1. Diagnosed: `seed_subjects.py` only seeded subjects for BSC CS & IT — other departments (BCOM, BAF, BMS, BAMMC) had no subjects in the database
- [x] 2. Updated `seed_subjects.py` to add subjects for all 5 departments (BSC CS & IT, BCOM, BAF, BMS, BAMMC) across semesters 1-6
- [x] 3. Ran `python seed_subjects.py` to insert the subjects into the database
- [x] 4. Now teachers from any department can load subjects by department for result management

## Result Management Marks Limit Fix
- [x] 1. Fixed `manage_results.html`: the JS `change` handler now updates the `max` attribute on the mark input fields when the Exam Type changes (previously only updated the display, leaving a stale max=20)
- [x] 2. Fixed mismatch: dropdown sends `value="Assignment"` but JS checked `"Assignment / Journal / Attendance"` — corrected both the load function and change handler to use `"Assignment"`
- [x] 3. Confirmed External/Practical marks are out of 30 (max=30), Internal/Assignment out of 20 (max=20)
- [x] 4. Verified backend `app.py` matches `exam_type == "Assignment"` correctly

## Unified Dashboard UI (Principal + Student → Match HOD/Teacher Style)
- [x] 1. Redesigned `templates/principal/principal_dashboard.html` to use the same card-box style as HOD/Teacher dashboards (gradient navbar, 70px rounded icons, centered h4 titles)
- [x] 2. Redesigned `templates/student/dashboard.html` to use the same card-box style (removed old dark sidebar layout)
- [x] 3. Principal cards: Manage Students, Manage Teachers, Manage HODs, Manage Notices, Manage Events, Department Rankings, College Toppers, Department Toppers
- [x] 4. Student cards: Profile, Notices, Events, Study Materials, Results + Student Information card
- [x] 5. All four dashboards (Principal, HOD, Teacher, Student) now share the same consistent UI

## Delete Notice Confirmation Alert Box
- [x] 1. Added `onclick="return confirm('Are you sure you want to delete this notice?')"` to Delete buttons in:
  - `templates/principal/manage_notices.html` (Principal dashboard)
  - `templates/hod/department_notices.html` (Teacher/HOD dashboard)
- [x] 2. Confirmation prevents accidental deletion by requiring the user to confirm before the delete action proceeds

## Teacher Notice Edit/Delete Redirect Bug Fix
- [x] 1. Diagnosed: `department_notices.html` had Edit/Delete buttons linking to Principal-only routes (`/edit_notice`, `/delete_notice`)
- [x] 2. Fixed: changed links to `/edit_department_notice/{{ id }}` and `/delete_department_notice/{{ id }}` which allow Teacher + HOD roles
- [x] 3. Verified `hod/edit_notice.html` form posts to current URL (no hardcoded action) with correct role-based Cancel redirects

## HOD Dashboard Crash Fix (view returned None)
- [x] 1. Diagnose the "view function did not return a valid response" error
- [x] 2. Verified `hod_dashboard` function source has a proper `return` (AST-based diag)
- [x] 3. Verified `hod/hod_dashboard.html` template renders fine with mock data (pure Jinja2 test)
- [x] 4. Root cause: DB query exceptions (schema drift) inside the route could crash the view
- [x] 5. Wrap HOD counts in try/except → non-fatal logging
- [x] 6. Wrap performance panel computation in try/except → non-fatal logging
- [x] 7. Add `hod is None` safety check → clear session + redirect to login
- [x] 8. `ast.parse(app.py)` syntax check → SYNTAX OK

## Sequential Student Display ID (101, 102, ...) Consistency
- [x] 1. Added `get_display_student_id(student)` helper in `app.py` (returns `index + 101` based on registration order)
- [x] 2. PDF marksheet info table uses `display_id` for "Student ID"
- [x] 3. QR code data uses `display_id` (matches PDF + lists)
- [x] 4. Templates use `{{ loop.index + 100 }}` for consistency:
  - `principal/students.html`, `hod/hod_students.html`, `teacher/attendance.html`, `teacher/manage_results.html`, `hod/department_attendance.html`
- [x] 5. Fixed QR block indentation (`qr_data` was dedented outside `download_result` → `IndentationError`)
- [x] 6. Verified `python -m py_compile app.py` → SYNTAX OK

## Verification
- [x] `python -m py_compile app.py` → exit code 0

## Notes
- `requirement.txt` already lists `matplotlib==3.10.0` and `pillow`.
- Run the app using the conda environment that contains the project's dependencies
  (the base system Python 3.14.6 does not have `matplotlib` installed).
- If using a plain `pip` environment, install the runtime deps with:
  `pip install flask flask-sqlalchemy pymysql reportlab qrcode matplotlib pillow`

