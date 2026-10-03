import io
import re
import csv
import openpyxl
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from accounts.permissions import IsInstructor
from curriculum.models import Topic
from assessments.models import Question, Choice
from assessments.serializers.instructor import InstructorQuestionSerializer

@extend_schema(tags=["Instructor Management"])
class InstructorQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for instructors to manage the question bank.
    Restricted to instructors (D15).

    D11: DELETE of a question that has recorded answers deactivates it
    (200, ``{"archived": true}``) instead of deleting the answers' target.
    Inactive questions are hidden unless ``?include_inactive=true``.
    """
    permission_classes = [IsInstructor]
    serializer_class = InstructorQuestionSerializer

    def get_queryset(self):
        queryset = Question.objects.select_related("topic").prefetch_related("choices")
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        if self.request.query_params.get("include_inactive", "").lower() not in ("1", "true"):
            queryset = queryset.filter(is_active=True)
        return queryset

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        try:
            with transaction.atomic():
                question.delete()
        except ProtectedError:
            Question.objects.filter(pk=question.pk).update(is_active=False)
            return Response({"id": question.pk, "archived": True}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)


def parse_excel_or_csv(file_obj, filename):
    rows = []
    if filename.lower().endswith(".csv"):
        content = file_obj.read().decode("utf-8-sig", errors="ignore")
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if row:
                rows.append([str(c).strip() for c in row])
    else:  # xlsx / xls
        wb = openpyxl.load_workbook(file_obj, data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(values_only=True):
            if row and any(row):
                rows.append([str(c).strip() if c is not None else "" for c in row])

    questions = []
    if rows and ("question" in str(rows[0][0]).lower() or "savol" in str(rows[0][0]).lower()):
        rows = rows[1:]

    for row in rows:
        if not row or not row[0]:
            continue
        q_text = str(row[0]).strip()
        options = [str(c).strip() for c in row[1:5] if str(c).strip()]
        if len(options) < 2:
            continue

        diff_val = 2
        if len(row) > 5 and row[5]:
            d_str = str(row[5]).lower()
            if "1" in d_str or "easy" in d_str or "oson" in d_str:
                diff_val = 1
            elif "3" in d_str or "hard" in d_str or "qiyin" in d_str:
                diff_val = 3

        explanation = str(row[6]).strip() if len(row) > 6 and row[6] else ""

        choices_data = []
        for idx, opt_text in enumerate(options):
            choices_data.append({
                "text": opt_text,
                "is_correct": (idx == 0)  # Rule: First answer option is ALWAYS CORRECT
            })

        questions.append({
            "text": q_text,
            "difficulty": diff_val,
            "explanation": explanation,
            "choices": choices_data
        })

    return questions


def parse_word_or_txt(file_obj, filename):
    lines = []
    if filename.lower().endswith(".docx"):
        import docx
        doc = docx.Document(file_obj)
        for p in doc.paragraphs:
            if p.text.strip():
                lines.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                r_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if r_cells:
                    lines.append("\t".join(r_cells))
    else:  # txt / doc
        content = file_obj.read().decode("utf-8", errors="ignore")
        lines = [line.strip() for line in content.splitlines() if line.strip()]

    questions = []
    # Check if lines are tab or comma delimited
    is_tabular = any("\t" in line for line in lines[:10])
    if is_tabular:
        for line in lines:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
            if len(parts) >= 3 and not ("question" in parts[0].lower() or "savol" in parts[0].lower()):
                q_text = parts[0]
                options = [p for p in parts[1:5] if p]
                diff_val = 2
                if len(parts) > 5:
                    d_str = parts[5].lower()
                    if "1" in d_str or "easy" in d_str: diff_val = 1
                    elif "3" in d_str or "hard" in d_str: diff_val = 3
                exp = parts[6] if len(parts) > 6 else ""
                choices_data = [{"text": opt, "is_correct": (i == 0)} for i, opt in enumerate(options)]
                questions.append({
                    "text": q_text,
                    "difficulty": diff_val,
                    "explanation": exp,
                    "choices": choices_data
                })
        return questions

    # Structured block parsing
    current_q = None
    q_pattern = r'^(question\s*\d*[\:\.\-]?|savol\s*\d*[\:\.\-]?|q\d*[\:\.\-]?|\d+[\.\)\:])\s*'
    opt_pattern = r'^[a-dA-D1-4][\.\)]\s*|^\-\s*|^\*\s*'

    for line in lines:
        if re.match(q_pattern, line, flags=re.I) and not re.match(opt_pattern, line):
            if current_q and len(current_q["choices"]) >= 2:
                questions.append(current_q)
            clean_q = re.sub(q_pattern, '', line, flags=re.I).strip()
            current_q = {"text": clean_q, "difficulty": 2, "explanation": "", "choices": []}
        elif current_q and re.match(opt_pattern, line):
            opt_text = re.sub(opt_pattern, '', line).strip()
            is_first = (len(current_q["choices"]) == 0)
            current_q["choices"].append({"text": opt_text, "is_correct": is_first})
        elif current_q and line.lower().startswith("difficulty:"):
            d_str = line.split(":", 1)[1].strip().lower()
            if "1" in d_str or "easy" in d_str or "oson" in d_str: current_q["difficulty"] = 1
            elif "3" in d_str or "hard" in d_str or "qiyin" in d_str: current_q["difficulty"] = 3
        elif current_q and line.lower().startswith("explanation:"):
            current_q["explanation"] = line.split(":", 1)[1].strip()

    if current_q and len(current_q["choices"]) >= 2:
        questions.append(current_q)

    return questions


@extend_schema(tags=["Instructor Management"])
class ImportQuestionsView(APIView):
    """
    POST /api/assessments/instructor/questions/import/
    Bulk imports test questions from uploaded Excel (.xlsx, .csv) or Word (.docx, .txt) files.
    RULE: The 1st answer option in the file for each question is marked as CORRECT. Options are shuffled when given to students.
    """
    permission_classes = [IsInstructor]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        topic_id = request.data.get("topic_id")
        file_obj = request.FILES.get("file")

        if not topic_id or not file_obj:
            return Response(
                {"detail": "Both 'topic_id' and 'file' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            topic = Topic.objects.get(pk=topic_id)
        except Topic.DoesNotExist:
            return Response(
                {"detail": f"Topic with id={topic_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        filename = file_obj.name.lower()
        if filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv"):
            parsed_questions = parse_excel_or_csv(file_obj, filename)
        elif filename.endswith(".docx") or filename.endswith(".doc") or filename.endswith(".txt"):
            parsed_questions = parse_word_or_txt(file_obj, filename)
        else:
            return Response(
                {"detail": "Unsupported file format. Please upload .xlsx, .csv, .docx, or .txt."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not parsed_questions:
            return Response(
                {"detail": "No valid question records found in file. Ensure the template format is followed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        created_count = 0
        with transaction.atomic():
            for q_item in parsed_questions:
                q_obj = Question.objects.create(
                    topic=topic,
                    text=q_item["text"],
                    difficulty=q_item["difficulty"],
                    explanation=q_item.get("explanation", ""),
                    is_active=True
                )
                choices_to_create = [
                    Choice(
                        question=q_obj,
                        text=c["text"],
                        is_correct=c["is_correct"]
                    )
                    for c in q_item["choices"]
                ]
                Choice.objects.bulk_create(choices_to_create)
                created_count += 1

        return Response({
            "detail": f"Successfully imported {created_count} questions for topic '{topic.name}'.",
            "imported_count": created_count
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Instructor Management"])
class DownloadQuestionTemplateView(APIView):
    """
    GET /api/assessments/instructor/templates/questions/?file_format=excel|word
    Downloads a sample template file ("shablon") with instructions that 1st option is ALWAYS the correct answer.
    """
    permission_classes = [IsInstructor]

    def perform_content_negotiation(self, request, force=False):
        # Override DRF content negotiation to prevent ?format=excel from triggering 404
        from rest_framework.renderers import JSONRenderer
        return (JSONRenderer(), 'application/json')

    def get(self, request):
        fmt = (request.query_params.get("file_format") or request.query_params.get("format") or "excel").lower()
        
        if fmt == "word":
            import docx
            doc = docx.Document()
            doc.add_heading("NeuroLearn Quiz Question Import Shablon (Word)", 0)
            doc.add_paragraph("Eslatma: Shablon faylida Har bir savolning BIRINCHI javobi (A option) TO'G'RI javob bo'lishi kerak. Talabaga test topshirishda javob variantlari avtomatik ravishda tasodifiy almashtiriladi (shuffled).")
            
            p1 = doc.add_paragraph()
            p1.add_run("Question 1: What is the time complexity of Binary Search?\n").bold = True
            p1.add_run("A) O(log n)\n")
            p1.add_run("B) O(n)\n")
            p1.add_run("C) O(n^2)\n")
            p1.add_run("D) O(1)\n")
            p1.add_run("Difficulty: Medium\n")
            p1.add_run("Explanation: Binary search repeatedly divides the search interval in half.")

            p2 = doc.add_paragraph()
            p2.add_run("Question 2: Which HTML tag is used for the main title?\n").bold = True
            p2.add_run("A) <h1>\n")
            p2.add_run("B) <head>\n")
            p2.add_run("C) <title>\n")
            p2.add_run("D) <header>\n")
            p2.add_run("Difficulty: Easy\n")
            p2.add_run("Explanation: <h1> defines the top-level main heading in HTML.")

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            response["Content-Disposition"] = 'attachment; filename="quiz_import_shablon.docx"'
            return response
        else:
            # Excel format
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Quiz Questions"
            
            headers = ["Question Text", "Correct Answer (1st Option)", "Option 2 (Incorrect)", "Option 3 (Incorrect)", "Option 4 (Incorrect)", "Difficulty (Easy/Medium/Hard)", "Explanation"]
            ws.append(headers)
            
            ws.append([
                "What is the time complexity of Binary Search?",
                "O(log n)",
                "O(n)",
                "O(n^2)",
                "O(1)",
                "Medium",
                "Binary search repeatedly divides the search interval in half."
            ])
            ws.append([
                "Which HTML tag is used for the main title?",
                "<h1>",
                "<head>",
                "<title>",
                "<header>",
                "Easy",
                "<h1> defines the top-level main heading in HTML."
            ])
            
            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            response["Content-Disposition"] = 'attachment; filename="quiz_import_shablon.xlsx"'
            return response


