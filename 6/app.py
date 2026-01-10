from flask import Flask, render_template, request, redirect, url_for
import sqlite3



app = Flask(__name__)

# ---------- ПІДКЛЮЧЕННЯ ДО БД ----------
def get_db():
    conn = sqlite3.connect("points.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------- ГОЛОВНА ----------
@app.route("/")
def home():
    return """
    <p><a href="/db-test">Перевірка БД</a></p>
    <p><a href="/points">Усі оцінки</a></p>
    <p><a href="/students">Студенти</a></p>
    <p><a href="/courses">Дисципліни</a></p>
<p><a href="/stats/avg-by-course">Середній бал по дисциплінах</a></p>
<p><a href="/stats/ects-by-course">ECTS по дисциплінах</a></p>
<p><a href="/stats/ects-by-student-semester">ECTS по студенту і семестру</a></p>


    """


# ---------- ПЕРЕВІРКА БД ----------
@app.route("/db-test")
def db_test():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM points").fetchone()[0]
    conn.close()
    return f"Кількість оцінок у базі: {count}"


# ---------- УСІ ОЦІНКИ ----------
@app.route("/points")
def points_all():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.id,
               s.name  AS student_name,
               c.title AS course_title,
               c.semester,
               p.value
        FROM points p
        JOIN student s ON s.id = p.id_student
        JOIN course  c ON c.id = p.id_course
        ORDER BY s.name, c.semester, c.title
    """).fetchall()
    conn.close()
    return render_template("points_all.html", rows=rows)


# ---------- СТУДЕНТИ ----------
@app.route("/students")
def students_list():
    conn = get_db()
    students = conn.execute("""
        SELECT id, name
        FROM student
        ORDER BY name
    """).fetchall()
    conn.close()
    return render_template("students.html", students=students)


# ---------- ОЦІНКИ КОНКРЕТНОГО СТУДЕНТА ----------
@app.route("/students/<int:student_id>/points")
def student_points(student_id):
    conn = get_db()

    student = conn.execute("""
        SELECT id, name
        FROM student
        WHERE id = ?
    """, (student_id,)).fetchone()

    rows = conn.execute("""
        SELECT p.id,
               c.title AS course_title,
               c.semester,
               p.value
        FROM points p
        JOIN course c ON c.id = p.id_course
        WHERE p.id_student = ?
        ORDER BY c.semester, c.title
    """, (student_id,)).fetchall()

    conn.close()
    return render_template("student_points.html", student=student, rows=rows)


# ---------- ДИСЦИПЛІНИ ----------
@app.route("/courses")
def courses_list():
    conn = get_db()
    courses = conn.execute("""
        SELECT id, title, semester
        FROM course
        ORDER BY semester, title
    """).fetchall()
    conn.close()
    return render_template("courses.html", courses=courses)


# ---------- РЕЙТИНГ ПО ДИСЦИПЛІНІ ----------
@app.route("/courses/<int:course_id>/rating")
def course_rating(course_id):
    conn = get_db()

    course = conn.execute("""
        SELECT id, title, semester
        FROM course
        WHERE id = ?
    """, (course_id,)).fetchone()

    rows = conn.execute("""
        SELECT s.name AS student_name, p.value
        FROM points p
        JOIN student s ON s.id = p.id_student
        WHERE p.id_course = ?
        ORDER BY p.value DESC, s.name
    """, (course_id,)).fetchall()

    conn.close()
    return render_template("course_rating.html", course=course, rows=rows)


# ---------- ЗАПУСК ----------
@app.route("/points/new", methods=["GET", "POST"])
def point_new():
    conn = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        course_id = request.form.get("course_id", type=int)
        value = request.form.get("value", type=int)

        conn.execute("""
            INSERT INTO points (id_course, id_student, value)
            VALUES (?, ?, ?)
        """, (course_id, student_id, value))
        conn.commit()
        conn.close()

        return redirect(url_for("points_all"))

    students = conn.execute("SELECT id, name FROM student ORDER BY name").fetchall()
    courses = conn.execute("SELECT id, title, semester FROM course ORDER BY semester, title").fetchall()
    conn.close()

    return render_template("point_new.html", students=students, courses=courses)

@app.route("/points/<int:point_id>/edit", methods=["GET", "POST"])
def point_edit(point_id):
    conn = get_db()

    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        course_id = request.form.get("course_id", type=int)
        value = request.form.get("value", type=int)

        conn.execute("""
            UPDATE points
            SET id_student = ?, id_course = ?, value = ?
            WHERE id = ?
        """, (student_id, course_id, value, point_id))
        conn.commit()
        conn.close()

        return redirect(url_for("points_all"))

    point = conn.execute("""
        SELECT id, id_student, id_course, value
        FROM points
        WHERE id = ?
    """, (point_id,)).fetchone()

    students = conn.execute("SELECT id, name FROM student ORDER BY name").fetchall()
    courses = conn.execute("SELECT id, title, semester FROM course ORDER BY semester, title").fetchall()

    conn.close()
    return render_template(
        "point_edit.html",
        point=point,
        students=students,
        courses=courses
    )

@app.route("/points/<int:point_id>/delete", methods=["GET", "POST"])
def point_delete(point_id):
    conn = get_db()

    if request.method == "POST":
        conn.execute("DELETE FROM points WHERE id = ?", (point_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("points_all"))

    point = conn.execute("""
        SELECT p.id,
               s.name AS student_name,
               c.title AS course_title,
               c.semester,
               p.value
        FROM points p
        JOIN student s ON s.id = p.id_student
        JOIN course  c ON c.id = p.id_course
        WHERE p.id = ?
    """, (point_id,)).fetchone()

    conn.close()
    return render_template("point_delete.html", point=point)

@app.route("/stats/avg-by-course")
def avg_by_course():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.title,
               c.semester,
               ROUND(AVG(p.value), 2) AS avg_value,
               COUNT(p.id) AS cnt
        FROM course c
        LEFT JOIN points p ON p.id_course = c.id
        GROUP BY c.id
        ORDER BY c.semester, c.title
    """).fetchall()
    conn.close()
    return render_template("avg_by_course.html", rows=rows)

@app.route("/stats/ects-by-course")
def ects_by_course():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.title,
               c.semester,
               CASE
                 WHEN p.value BETWEEN 90 AND 100 THEN 'A'
                 WHEN p.value BETWEEN 82 AND 89  THEN 'B'
                 WHEN p.value BETWEEN 75 AND 81  THEN 'C'
                 WHEN p.value BETWEEN 67 AND 74  THEN 'D'
                 WHEN p.value BETWEEN 60 AND 66  THEN 'E'
                 WHEN p.value BETWEEN 35 AND 59  THEN 'FX'
                 WHEN p.value BETWEEN 0  AND 34  THEN 'F'
                 ELSE 'N/A'
               END AS ects,
               COUNT(*) AS cnt
        FROM points p
        JOIN course c ON c.id = p.id_course
        GROUP BY c.id, ects
        ORDER BY c.semester, c.title,
                 CASE ects
                   WHEN 'A' THEN 1
                   WHEN 'B' THEN 2
                   WHEN 'C' THEN 3
                   WHEN 'D' THEN 4
                   WHEN 'E' THEN 5
                   WHEN 'FX' THEN 6
                   WHEN 'F' THEN 7
                   ELSE 8
                 END
    """).fetchall()
    conn.close()
    return render_template("ects_by_course.html", rows=rows)

@app.route("/stats/ects-by-student-semester")
def ects_by_student_semester():
    conn = get_db()
    rows = conn.execute("""
        SELECT s.name AS student_name,
               c.semester,
               CASE
                 WHEN p.value BETWEEN 90 AND 100 THEN 'A'
                 WHEN p.value BETWEEN 82 AND 89  THEN 'B'
                 WHEN p.value BETWEEN 75 AND 81  THEN 'C'
                 WHEN p.value BETWEEN 67 AND 74  THEN 'D'
                 WHEN p.value BETWEEN 60 AND 66  THEN 'E'
                 WHEN p.value BETWEEN 35 AND 59  THEN 'FX'
                 WHEN p.value BETWEEN 0  AND 34  THEN 'F'
                 ELSE 'N/A'
               END AS ects,
               COUNT(*) AS cnt
        FROM points p
        JOIN student s ON s.id = p.id_student
        JOIN course  c ON c.id = p.id_course
        GROUP BY s.id, c.semester, ects
        ORDER BY s.name, c.semester,
                 CASE ects
                   WHEN 'A' THEN 1
                   WHEN 'B' THEN 2
                   WHEN 'C' THEN 3
                   WHEN 'D' THEN 4
                   WHEN 'E' THEN 5
                   WHEN 'FX' THEN 6
                   WHEN 'F' THEN 7
                   ELSE 8
                 END
    """).fetchall()
    conn.close()
    return render_template("ects_by_student_semester.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)
