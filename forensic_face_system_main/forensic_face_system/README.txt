================================================
 AI-Driven Forensic Face Sketch System
 @Jerusalem College of Engineering
================================================

REQUIREMENTS
------------
Install dependencies:
    pip install Pillow numpy deepface opencv-python

FOLDER STRUCTURE
----------------
forensic_face_system/
├── login.py          ← Start here (main entry point)
├── main_menu.py      ← Home screen after login
├── sketch_creator.py ← Build composite sketch from face parts
├── upload_match.py   ← Upload sketch & find matching face
├── faces/            ← Put reference face images HERE (.jpg/.png)
└── sketches/         ← Saved sketch output goes here

HOW TO RUN
----------
    python login.py

DEFAULT CREDENTIALS
-------------------
Username: admin      Password: admin123
Username: officer    Password: police123
Username: dept       Password: dept2024

ADDING FACE DATABASE
--------------------
Copy reference face photos (.jpg or .png) into the /faces/ folder.
These are the images the system searches through when finding a match.
More photos = better accuracy.

HOW IT WORKS
------------
1. Login with department credentials
2. Choose:
   a) Create a Sketch – pick Head, Hair, Eyes, Eyebrows, Nose,
      Lips, Mustache etc. from side galleries → compose face → Save
   b) Upload Sketch – browse any sketch/photo → Upload → Find Match
3. Find Match compares the sketch against all faces in /faces/
   using DeepFace (VGG-Face model) for deep feature similarity,
   with a histogram cosine-similarity fallback if DeepFace fails.
4. Result shows: matched photo, similarity %, confidence score.

NOTES
-----
• First run may download VGG-Face weights (~500MB) automatically.
• Works best when sketch and database face are same gender/angle.
• enforce_detection=False allows matching even without a clear face.
