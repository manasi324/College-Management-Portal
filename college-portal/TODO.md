# Marksheet PDF Enhancement - Task Tracker

## Plan
- [x] Analyze current app.py & confirm requirements with user
- [x] Fix existing errors (HRFlowable import, send_file syntax, redirect)

## Enhancements
- [x] 1. Add imports (matplotlib, PIL) for graph & placeholder image generation
- [x] 2. Add helper functions (get_seat_number, ensure_static_assets, generate_student_photo, generate_sgpa_graph)
- [x] 3. Add Seat/Roll number + Student photograph in info section
- [x] 4. Fix marks table column widths (10 columns)
- [x] 5. Add Semester-wise SGPA table
- [x] 6. Add Semester-wise SGPA bar graph (matplotlib)
- [x] 7. Add Principal & COE digital signature images in footer
- [x] 8. Add Official college seal/stamp in footer
- [x] 9. Add QR verification text below QR code
- [x] 10. Add Result Declaration note
- [x] 11. Add "ROYAL COLLEGE" watermark behind content
- [x] 12. Verify with `python -m py_compile app.py` → exit code 0

## Additional Fix
- [x] 13. Add missing `/view_results` route (was referenced by `edit_result` & `delete_result` redirects)
- [x] 14. Create `templates/teacher/view_results.html` so the redirects don't 404
- [x] 15. Verify with `python -m py_compile app.py` → exit code 0

## Notes
- `requirement.txt` already lists `matplotlib==3.10.0` and `pillow`.
- Run the app using the conda environment that contains the project's dependencies
  (the base system Python 3.14.6 does not have `matplotlib` installed).
- If using a plain `pip` environment, install the runtime deps with:
  `pip install flask flask-sqlalchemy pymysql reportlab qrcode matplotlib pillow`

