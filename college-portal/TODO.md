# College Management Portal - Task Tracker

## Marks Distribution Change (Non-CS&IT Departments)
Goal: For all departments EXCEPT "BSC CS & IT", change marks scheme to:
- External: 60 (theory)
- Internal: 20
- Others (assignment/ppt/attendance): 20
- Practical: 0 (not applicable)
- Total: 100

BSC CS & IT keeps existing scheme: Internal=20, Assignment=20, External=30, Practical=30.

- [x] 1. Add `get_marks_scheme(department_name)` helper in `app.py`
- [x] 2. Pass `marks_scheme` to `manage_results`, `edit_result`, `student_result`, `download_result` routes
- [x] 3. Relabel "Assignment" column to "Others" for non-CS&IT in view/student templates
- [x] 4. Update `manage_results.html` JS to be department-aware (External→60, others→20, practical not applicable)
- [x] 5. Update `edit_result.html` max values using scheme
- [x] 6. Update `student_result.html` max values using scheme
- [x] 7. Verify with `python -m py_compile app.py`
