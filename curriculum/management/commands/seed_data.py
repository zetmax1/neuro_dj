import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from django.utils.timezone import now
from django.db import transaction
from curriculum.models import Topic, TopicResource
from assessments.models import (
    Question, 
    Choice, 
    UserKnowledgeState, 
    UserKnowledgeHistory, 
    AssessmentAttempt, 
    DifficultyLevel, 
    MasteryLevel
)
from accounts.demo import DemoPassword, non_demo_users
from accounts.models import CustomUser

class Command(BaseCommand):
    help = (
        "DESTRUCTIVE: deletes ALL topics, questions, attempts and learner states, then "
        "seeds a demo curriculum. Requires --yes-delete-all and refuses to run when "
        "non-demo user accounts exist."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes-delete-all",
            action="store_true",
            help="Confirm that every curriculum and assessment row may be deleted.",
        )

    def handle(self, *args, **options):
        if not options["yes_delete_all"]:
            raise CommandError(
                "seed_data deletes all curriculum and assessment data. "
                "Re-run with --yes-delete-all to confirm."
            )
        real_users = non_demo_users().count()
        if real_users:
            raise CommandError(
                f"Refusing to run: {real_users} non-demo user account(s) exist and their "
                "learning data would be destroyed. Use a fresh database."
            )
        demo_password = DemoPassword(self.stdout)
        self.stdout.write("Starting database seeding...")

        with transaction.atomic():
            # 1. Clear existing data
            self.stdout.write("Clearing existing curriculum and assessment data...")
            Choice.objects.all().delete()
            Question.objects.all().delete()
            AssessmentAttempt.objects.all().delete()
            UserKnowledgeState.objects.all().delete()
            UserKnowledgeHistory.objects.all().delete()
            TopicResource.objects.all().delete()
            Topic.objects.all().delete()

            # 2. Create Curriculum Tree
            self.stdout.write("Creating topics...")
            
            cs = Topic.objects.create(
                name="Computer Science",
                slug="computer-science",
                description="The foundational study of computation, information theory, and programming paradigms.",
                position=1,
                is_unlocked=True
            )

            ds = Topic.objects.create(
                name="Data Structures",
                slug="data-structures",
                description="Core structures for organizing, managing, and storing data efficiently.",
                parent=cs,
                position=1,
                is_unlocked=True
            )

            algo = Topic.objects.create(
                name="Algorithms",
                slug="algorithms",
                description="Step-by-step computational procedures for solving complex mathematical and logical problems.",
                parent=cs,
                position=2,
                is_unlocked=True
            )

            binary_trees = Topic.objects.create(
                name="Binary Trees",
                slug="binary-trees",
                description="Hierarchical tree structures where each node has at most two children.",
                parent=ds,
                position=1,
                is_unlocked=True
            )

            hash_maps = Topic.objects.create(
                name="Hash Maps",
                slug="hash-maps",
                description="Key-value mapping data structures utilizing hashing functions for constant-time lookup.",
                parent=ds,
                position=2,
                is_unlocked=True
            )

            sorting = Topic.objects.create(
                name="Sorting",
                slug="sorting",
                description="Algorithms for rearranging elements of a list in a specified ordering (numerical or lexicographical).",
                parent=algo,
                position=1,
                is_unlocked=True
            )

            graphs = Topic.objects.create(
                name="Graph Traversals",
                slug="graph-traversals",
                description="Techniques for visiting all nodes in graph network configurations (BFS and DFS).",
                parent=algo,
                position=2,
                is_unlocked=True
            )

            all_topics = [cs, ds, algo, binary_trees, hash_maps, sorting, graphs]

            # 3. Create Resources
            self.stdout.write("Creating resources for topics...")
            resources_data = {
                cs: [
                    ("Introduction to Computer Science Lecture", TopicResource.ResourceType.VIDEO, "https://www.youtube.com/embed/dQw4w9WgXcQ", "A foundational video explaining computation."),
                    ("CS Fundamentals Cheat Sheet", TopicResource.ResourceType.TEXT_CONTENT, "", "Welcome to Computer Science! Focus on Big-O complexity, logic gates, and low-level memory layout.")
                ],
                ds: [
                    ("Data Structures Overview Notes", TopicResource.ResourceType.TEXT_CONTENT, "", "Arrays, LinkedLists, Stacks, Queues: choose your storage structures carefully based on runtime complexity constraints.")
                ],
                binary_trees: [
                    ("Binary Trees & BST Crash Course", TopicResource.ResourceType.VIDEO, "https://www.youtube.com/embed/H5J1LH8yXyg", "Learn pre-order, in-order, and post-order depth-first traversals."),
                    ("BST Traversal Reference Doc", TopicResource.ResourceType.TEXT_CONTENT, "", "A binary search tree maintains sorted elements: left children < root < right children. Average search complexity is O(log n).")
                ],
                hash_maps: [
                    ("Understanding Hash Collisions", TopicResource.ResourceType.VIDEO, "https://www.youtube.com/embed/sfWbdyeffvk", "Visualizing separate chaining and open addressing collision resolution strategies.")
                ],
                sorting: [
                    ("QuickSort vs MergeSort", TopicResource.ResourceType.TEXT_CONTENT, "", "QuickSort uses partition pivots (O(n log n) average, O(n^2) worst). MergeSort splits arrays in half and merges them in O(n log n) stable time.")
                ],
                graphs: [
                    ("BFS and DFS Depth Analysis", TopicResource.ResourceType.VIDEO, "https://www.youtube.com/embed/pcKY4hjDrxk", "Using queues for Breadth-First search and stacks/recursion for Depth-First search.")
                ]
            }

            for topic, res_list in resources_data.items():
                for title, res_type, url, note in res_list:
                    TopicResource.objects.create(
                        topic=topic,
                        title=title,
                        resource_type=res_type,
                        external_url=url,
                        content=note
                    )

            # 4. Create Questions & Choices
            self.stdout.write("Creating questions...")
            questions_data = [
                # Binary Trees Questions
                {
                    "topic": binary_trees,
                    "text": "What is the worst-case time complexity of searching in a standard (unbalanced) Binary Search Tree (BST)?",
                    "explanation": "If the tree becomes skewed (like a linked list), searching takes linear time O(n).",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "choices": [
                        ("O(1)", False),
                        ("O(log n)", False),
                        ("O(n)", True),
                        ("O(n log n)", False)
                    ]
                },
                {
                    "topic": binary_trees,
                    "text": "Which tree traversal visits the root node first, then the left subtree, and finally the right subtree?",
                    "explanation": "Pre-order traversal visits Node, then Left, then Right (N-L-R).",
                    "difficulty": DifficultyLevel.EASY,
                    "choices": [
                        ("In-order", False),
                        ("Pre-order", True),
                        ("Post-order", False),
                        ("Level-order", False)
                    ]
                },
                {
                    "topic": binary_trees,
                    "text": "In a self-balancing binary search tree like an AVL tree, what is the maximum height difference allowed between the left and right subtrees of any node?",
                    "explanation": "An AVL tree maintains balance by ensuring the height difference (balance factor) is at most 1.",
                    "difficulty": DifficultyLevel.HARD,
                    "choices": [
                        ("0", False),
                        ("1", True),
                        ("2", False),
                        ("Unlimited", False)
                    ]
                },

                # Hash Maps Questions
                {
                    "topic": hash_maps,
                    "text": "What is the average-case time complexity of retrieving a value by its key from a Hash Map?",
                    "explanation": "On average, hashing maps keys directly to buckets in constant time O(1).",
                    "difficulty": DifficultyLevel.EASY,
                    "choices": [
                        ("O(1)", True),
                        ("O(log n)", False),
                        ("O(n)", False),
                        ("O(n log n)", False)
                    ]
                },
                {
                    "topic": hash_maps,
                    "text": "Which collision resolution technique stores all colliding elements in a linked list linked to the hash bucket?",
                    "explanation": "Separate chaining stores collisions outside the hash table using linked structures.",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "choices": [
                        ("Linear Probing", False),
                        ("Quadratic Probing", False),
                        ("Double Hashing", False),
                        ("Separate Chaining", True)
                    ]
                },

                # Sorting Questions
                {
                    "topic": sorting,
                    "text": "Which of the following sorting algorithms is stable and guarantees a worst-case time complexity of O(n log n)?",
                    "explanation": "Merge sort is stable and guarantees O(n log n) runtime by splitting and merging subarrays.",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "choices": [
                        ("Quick Sort", False),
                        ("Merge Sort", True),
                        ("Selection Sort", False),
                        ("Bubble Sort", False)
                    ]
                },
                {
                    "topic": sorting,
                    "text": "What is the best-case time complexity of Bubble Sort when optimized with a flag to check if any swaps were made?",
                    "explanation": "If the array is already sorted, Bubble Sort makes one pass of O(n) comparisons and stops.",
                    "difficulty": DifficultyLevel.EASY,
                    "choices": [
                        ("O(1)", False),
                        ("O(n)", True),
                        ("O(n log n)", False),
                        ("O(n^2)", False)
                    ]
                },

                # Graphs Questions
                {
                    "topic": graphs,
                    "text": "Which data structure is typically utilized to implement Breadth-First Search (BFS) on a graph?",
                    "explanation": "BFS explores neighbors level-by-level using a FIFO Queue.",
                    "difficulty": DifficultyLevel.EASY,
                    "choices": [
                        ("Queue", True),
                        ("Stack", False),
                        ("Priority Queue", False),
                        ("Binary Tree", False)
                    ]
                },
                {
                    "topic": graphs,
                    "text": "Which algorithm is commonly used to find the shortest path in a weighted graph with non-negative edge weights?",
                    "explanation": "Dijkstra's algorithm solves single-source shortest path in weighted graphs in O(E + V log V) time.",
                    "difficulty": DifficultyLevel.MEDIUM,
                    "choices": [
                        ("Kruskal's Algorithm", False),
                        ("Dijkstra's Algorithm", True),
                        ("Prim's Algorithm", False),
                        ("Floyd-Warshall Algorithm", False)
                    ]
                }
            ]

            for q_info in questions_data:
                question = Question.objects.create(
                    topic=q_info["topic"],
                    text=q_info["text"],
                    explanation=q_info["explanation"],
                    difficulty=q_info["difficulty"]
                )
                for choice_text, is_correct in q_info["choices"]:
                    Choice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=is_correct
                    )

            # 5. Populate Student States for yuta@gmail.com
            self.stdout.write("Populating learning analytics and states for user 'yuta@gmail.com'...")
            try:
                user = CustomUser.objects.get(email="yuta@gmail.com")
            except CustomUser.DoesNotExist:
                user = CustomUser.objects.create_user(
                    email="yuta@gmail.com",
                    password=demo_password.value,
                    first_name="Yuta",
                    last_name="Okkotsu"
                )

            # Assign knowledge states to topics
            # Computer Science: Mastered
            UserKnowledgeState.objects.create(
                user=user,
                topic=cs,
                mastery_level=MasteryLevel.MASTERED,
                mastery_percentage=0.95,
                score=92,
                total_attempts=24,
                correct_attempts=22,
                streak=8
            )
            UserKnowledgeHistory.objects.create(
                user=user,
                topic=cs,
                calculated_mastery=0.95,
                algorithm_used="bkt"
            )

            # Data Structures: Intermediate
            UserKnowledgeState.objects.create(
                user=user,
                topic=ds,
                mastery_level=MasteryLevel.INTERMEDIATE,
                mastery_percentage=0.68,
                score=78,
                total_attempts=15,
                correct_attempts=12,
                streak=3
            )
            UserKnowledgeHistory.objects.create(
                user=user,
                topic=ds,
                calculated_mastery=0.68,
                algorithm_used="bkt"
            )

            # Binary Trees: Beginner
            UserKnowledgeState.objects.create(
                user=user,
                topic=binary_trees,
                mastery_level=MasteryLevel.BEGINNER,
                mastery_percentage=0.45,
                score=60,
                total_attempts=8,
                correct_attempts=5,
                streak=1
            )
            UserKnowledgeHistory.objects.create(
                user=user,
                topic=binary_trees,
                calculated_mastery=0.45,
                algorithm_used="bkt"
            )

            # Hash Maps: Advanced
            UserKnowledgeState.objects.create(
                user=user,
                topic=hash_maps,
                mastery_level=MasteryLevel.ADVANCED,
                mastery_percentage=0.82,
                score=85,
                total_attempts=12,
                correct_attempts=10,
                streak=5
            )
            UserKnowledgeHistory.objects.create(
                user=user,
                topic=hash_maps,
                calculated_mastery=0.82,
                algorithm_used="bkt"
            )

            # Algorithms: Not Started
            UserKnowledgeState.objects.create(
                user=user,
                topic=algo,
                mastery_level=MasteryLevel.NOT_STARTED,
                mastery_percentage=0.0,
                score=0,
                total_attempts=0,
                correct_attempts=0,
                streak=0
            )

            # Sorting: Not Started
            UserKnowledgeState.objects.create(
                user=user,
                topic=sorting,
                mastery_level=MasteryLevel.NOT_STARTED,
                mastery_percentage=0.0,
                score=0,
                total_attempts=0,
                correct_attempts=0,
                streak=0
            )

            # Graphs: Not Started
            UserKnowledgeState.objects.create(
                user=user,
                topic=graphs,
                mastery_level=MasteryLevel.NOT_STARTED,
                mastery_percentage=0.0,
                score=0,
                total_attempts=0,
                correct_attempts=0,
                streak=0
            )

            # 6. Generate historical attempts for activity metrics
            self.stdout.write("Creating mock history logs...")
            # We want to create attempts in the past 7 days to populate the weekly progress and chart.
            current_time = now()
            random.seed(42)
            
            # Select some questions to create attempts
            all_questions = list(Question.objects.all())
            for day in range(7):
                attempt_date = current_time - timedelta(days=6 - day)
                # Create 2-3 attempts per day
                for _ in range(random.randint(2, 4)):
                    question = random.choice(all_questions)
                    correct_choice = question.choices.filter(is_correct=True).first()
                    incorrect_choice = question.choices.filter(is_correct=False).first()
                    
                    is_correct = random.random() < 0.8  # 80% correct probability
                    selected = correct_choice if is_correct else incorrect_choice

                    attempt = AssessmentAttempt.objects.create(
                        user=user,
                        question=question,
                        selected_choice=selected,
                        is_correct=is_correct
                    )
                    # Hack back-date created/answered field
                    AssessmentAttempt.objects.filter(pk=attempt.pk).update(answered_at=attempt_date)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully!"))
