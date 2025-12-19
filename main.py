from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import mimetypes
from socketserver import ThreadingMixIn
from models import Teacher, Room, SchoolClass, TimeSlot, ScheduleResponse
from solver import SchoolScheduler

# Threading server to handle multiple requests if needed (though basic runs single threaded mostly)
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class SchedulerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve static files
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('static/index.html')
        elif self.path.startswith('/static/'):
            # Security check: prevent ../ traversal
            safe_path = os.path.normpath(self.path).lstrip('/')
            if not safe_path.startswith('static/'):
               self.send_error(403, "Forbidden")
               return
            self.serve_file(safe_path)
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == '/api/solve':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)

                # Parse data into models
                teachers = [Teacher.from_dict(t) for t in data.get('teachers', [])]
                rooms = [Room.from_dict(r) for r in data.get('rooms', [])]
                classes = [SchoolClass.from_dict(c) for c in data.get('classes', [])]
                time_slots = [TimeSlot.from_dict(t) for t in data.get('time_slots', [])]

                # Run Solver
                solver = SchoolScheduler(teachers, rooms, classes, time_slots)
                result = solver.solve()

                # Send Response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result.to_dict()).encode())

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_error(500, f"Server Error: {str(e)}")
        else:
            self.send_error(404, "Endpoint not found")

    def serve_file(self, filepath):
        try:
            # Resolve relative to current directory
            full_path = os.path.join(os.getcwd(), filepath)
            if not os.path.exists(full_path):
                self.send_error(404, "File not found")
                return

            # Guess mime type
            ctype, _ = mimetypes.guess_type(full_path)
            if ctype is None:
                ctype = 'application/octet-stream'

            with open(full_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

def run(server_class=ThreadingHTTPServer, handler_class=SchedulerHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
