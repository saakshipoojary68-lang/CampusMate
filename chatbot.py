import json
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = os.path.dirname(os.path.abspath(__file__))

class CampusMateBot:
    def __init__(self):
        with open(os.path.join(ROOT, "staff_data.json"), encoding="utf-8") as f:
            self.staff = json.load(f)["departments"]
        with open(os.path.join(ROOT, "faq_data.json"), encoding="utf-8") as f:
            self.faqs = json.load(f)
        with open(os.path.join(ROOT, "hostel_rules.json"), encoding="utf-8") as f:
            self.hostel = json.load(f)
        with open(os.path.join(ROOT, "bus_routes.json"), encoding="utf-8") as f:
            self.bus_data = json.load(f)
        with open(os.path.join(ROOT, "canteen_data.json"), encoding="utf-8") as f:
            self.canteen_data = json.load(f)
        with open(os.path.join(ROOT, "library_data.json"), encoding="utf-8") as f:
            self.library_data = json.load(f)
        with open(os.path.join(ROOT, "college_info.json"), encoding="utf-8") as f:
            self.college_info = json.load(f)
        with open(os.path.join(ROOT, "academic_calendar.json"), encoding="utf-8") as f:
            self.academic_calendar = json.load(f)
        with open(os.path.join(ROOT, "holiday_data.json"), encoding="utf-8") as f:
            self.holiday_data = json.load(f)
        with open(os.path.join(ROOT, "fee_data.json"), encoding="utf-8") as f:
            self.fee_data = json.load(f)
        with open(os.path.join(ROOT, "admission_data.json"), encoding="utf-8") as f:
            self.admission_data = json.load(f)
        with open(os.path.join(ROOT, "events_data.json"), encoding="utf-8") as f:
            self.events_data = json.load(f)
        self.questions = [q for item in self.faqs for q in item["questions"]]
        self.answers = [item["answer"] for item in self.faqs for _ in item["questions"]]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform(self.questions) if self.questions else None

    def get_departments(self):
        return [{"code": code, "name": dept["full_name"]} for code, dept in self.staff.items()]

    def _department_code(self, message):
        q = message.lower()
        aliases = {
            "CSE": ["cse", "computer science and engineering", "computer science engineering"],
            "ECE": ["ece", "electronics and communication", "electronics and communication engineering"],
            "CSBS": ["csbs", "computer science and business systems"],
            "AIML": ["ai & ml", "ai and ml", "aiml", "artificial intelligence and machine learning"],
            "AIDS": ["ai & ds", "ai and ds", "aids", "artificial intelligence and data science"],
            "CSD": ["csd", "computer science and design"],
            "ME": ["mechanical", "mechanical engineering"],
            "ISE": ["ise", "information science", "information science and engineering"],
            "FIRST_YEAR": ["first year", "science and humanities", "first year science"]
        }
        for code, terms in aliases.items():
            if any(term in q for term in terms):
                return code
        return None

    def _format_people(self, rows):
        if not rows:
            return "No staff details are currently listed for that category."
        return "\n".join(f"• {name} — {designation}" for name, designation in rows)

    def _department_answer(self, message):
        code = self._department_code(message)
        if not code:
            return None
        dept = self.staff[code]
        q = message.lower()
        if any(word in q for word in ["hod", "head of department", "head of the department"]):
            h = dept["hod"]
            return f"{dept['full_name']} HOD: {h['name']} — {h['designation']}."
        if any(word in q for word in ["technical", "lab staff", "technical staff", "programmer", "foreman"]):
            return f"{dept['full_name']} – Technical Staff:\n" + self._format_people(dept.get("technical_staff", []))
        if any(word in q for word in ["faculty", "teaching staff", "teaching faculty", "professor", "lecturer", "staff list", "all staff", "all faculty"]):
            if "subject_groups" in dept:
                groups = dept["subject_groups"]
                selected_subjects = [subject for subject in groups if subject.lower() in q]
                if selected_subjects:
                    return (f"{dept['full_name']} – {selected_subjects[0]} Faculty:\n"
                            + self._format_people(groups[selected_subjects[0]]))
                parts = []
                for subject, people in groups.items():
                    parts.append(f"{subject}:\n{self._format_people(people)}")
                return f"{dept['full_name']} – Teaching Faculty\n\n" + "\n\n".join(parts)
            # HOD details are stored separately; avoid repeating the HOD in the teaching-faculty list.
            hod = dept.get("hod", {})
            people = [person for person in dept.get("teaching_faculty", [])
                      if not (person[0] == hod.get("name") and person[1] == hod.get("designation"))]
            return f"{dept['full_name']} – Teaching Faculty:\n" + self._format_people(people)
        if "subject_groups" in dept:
            subjects = ", ".join(dept["subject_groups"].keys())
            return f"{dept['full_name']} includes these subject groups in this knowledge base: {subjects}. Ask for a subject's faculty, the HOD, or technical staff."
        return f"{dept['full_name']} is included in CampusMate. Ask for its HOD, teaching faculty, or technical staff."


    def _hostel_answer(self, message):
        q = message.lower()
        hostel_terms = ["hostel", "hosteller", "outpass", "warden", "hostel rules", "hostel rule"]
        if not any(term in q for term in hostel_terms):
            return None

        # Answer warden questions from the separately supplied hostel assignment list.
        if "warden" in q or "warden" in q:
            wardens = self.hostel.get("wardens", {})
            if any(term in q for term in ["boys", "boy's", "male"]):
                rows = wardens.get("Boys' Hostel", [])
                heading = "Boys' Hostel Wardens"
            elif any(term in q for term in ["girls", "girl's", "female"]):
                rows = wardens.get("Girls' Hostel", [])
                heading = "Girls' Hostel Wardens"
            else:
                rows = []
                for hostel_name, people in wardens.items():
                    rows.append((hostel_name, people))
                output = ["Hostel Warden Details:"]
                for hostel_name, people in rows:
                    output.append(f"\n{hostel_name}:")
                    output.extend(f"• {person['name']} — {person['designation']}" for person in people)
                output.append(f"\nNote: {self.hostel.get('warden_note', 'Contact details are not available in the current knowledge base.')}")
                return "\n".join(output)
            output = [f"{heading}:"]
            output.extend(f"• {person['name']} — {person['designation']}" for person in rows)
            output.append(f"\nNote: {self.hostel.get('warden_note', 'Contact details are not available in the current knowledge base.')}")
            return "\n".join(output)

        sections = self.hostel["sections"]
        if any(term in q for term in ["all rules", "all hostel", "complete rules", "hostel rules", "hostel rule book", "rules of hostel"]):
            output = [f"Hostel rules from the supplied rule book (dated {self.hostel['document_date']}):"]
            for section in sections:
                output.append(f"\n{section['title']}:")
                output.extend(f"• {rule}" for rule in section["rules"])
            output.append(f"\nNote: {self.hostel['note']}")
            return "\n".join(output)

        keywords = {
            "Attendance and Outpass": ["attendance", "outpass", "out pass", "outing", "leave hostel", "return time", "hostel timing", "curfew", "college premises"],
            "Hostel Cleanliness and Hygiene": ["clean", "cleanliness", "hygiene", "damage", "dustbin", "litter", "bathroom", "furniture", "room cleaning"],
            "Etiquette, Discipline and Safety": ["discipline", "ragging", "outsider", "day scholar", "parent", "parents visit", "key", "lost key", "valuables", "safety"],
            "Other Guidelines": ["electricity", "water", "mess", "pay and eat", "pay & eat", "medical", "insurance", "grievance", "complaint", "between semester", "during exams"]
        }
        matches = []
        for section in sections:
            if any(term in q for term in keywords[section["title"]]):
                matches.append(section)
        if not matches:
            # If the user asks generally about hostel, provide the section headings and source caveat.
            headings = ", ".join(section["title"] for section in sections)
            return (f"I have hostel information in these sections: {headings}. "
                    "Ask about outpass, attendance timings, cleanliness, discipline, visitors, mess, medical emergencies or other rules. "
                    f"The supplied rule book is dated {self.hostel['document_date']}.")
        output = []
        for section in matches:
            output.append(f"{section['title']}:")
            output.extend(f"• {rule}" for rule in section["rules"])
        output.append(f"\nSource note: {self.hostel['note']}")
        return "\n".join(output)


    def _bus_answer(self, message):
        q = message.lower()
        bus_terms = ["bus", "transport", "route", "bus stop", "bus timing", "bus coordinator"]
        if not any(term in q for term in bus_terms):
            return None

        routes = self.bus_data.get("routes", [])
        # Route-specific questions such as "Route 2" or "bus number 2".
        match = re.search(r"\b(?:route|bus)\s*(?:no\.?|number)?\s*(\d{1,2})\b", q)
        if match:
            route_no = int(match.group(1))
            route = next((r for r in routes if r["route_no"] == route_no), None)
            if not route:
                if route_no == 13:
                    return "Route 13 details have not been provided in the current CampusMate knowledge base. Please contact the transport coordinator."
                return f"I don't have details for Route {route_no} in the current bus information."
            return (f"Bus Route {route['route_no']} (Bus No. {route['bus_no']})\n"
                    f"Departure Time: {route['departure_time']}\n"
                    f"Stops: {route['stops']}\n"
                    f"Coordinator: {route['coordinator']}\n"
                    f"Contact No: {route['contact_no']}")

        # Find routes containing a place mentioned in the user's question.
        place_terms = [word for word in re.findall(r"[a-zA-Z]+", q)
                       if len(word) >= 4 and word not in {"which", "route", "does", "this", "that", "college", "bus", "stop", "goes", "from", "with", "tell", "about", "details", "timing", "contact", "number", "coordinator", "transport"}]
        place_matches = []
        for route in routes:
            stops_lower = route["stops"].lower()
            if any(term in stops_lower for term in place_terms):
                place_matches.append(route)
        if place_matches:
            output = ["Bus routes matching the place you mentioned:"]
            for r in place_matches:
                output.append(f"\nRoute {r['route_no']} (Bus {r['bus_no']}) — {r['departure_time']}\n"
                              f"Stops: {r['stops']}\nCoordinator: {r['coordinator']} | Contact: {r['contact_no']}")
            return "\n".join(output) + "\n\n" + self.bus_data.get("note", "")

        if any(word in q for word in ["all", "list", "routes", "bus facilities", "bus facility", "transport details"]):
            output = ["College Bus Routes:"]
            for r in routes:
                output.append(f"Route {r['route_no']} (Bus {r['bus_no']}) — {r['departure_time']} | Coordinator: {r['coordinator']} | Contact: {r['contact_no']}\nStops: {r['stops']}")
            output.append("\nNote: " + self.bus_data.get("note", ""))
            return "\n\n".join(output)

        return ("I can provide bus route details, departure times, stops, coordinators and contact numbers. "
                "Ask about a route number (for example, 'Route 2 details') or a stop (for example, 'Which bus goes through Puttur?').")

    def _canteen_answer(self, message):
        q = message.lower()
        canteen_terms = ["canteen", "cafeteria", "can cafe", "can express"]
        if not any(term in q for term in canteen_terms):
            return None

        canteens = self.canteen_data.get("canteens", [])
        aliases = {
            "CEC Canteen": ["cec canteen", "cec cafeteria", "main canteen"],
            "Can Cafe": ["can cafe", "cancafe", "cafe"],
            "Can Express": ["can express", "canexpress", "express canteen"]
        }
        selected = None
        for canteen in canteens:
            names = [canteen["name"].lower()] + aliases.get(canteen["name"], [])
            if any(name in q for name in names):
                selected = canteen
                break

        if selected is None:
            output = ["The college has three canteens listed in CampusMate:"]
            output.extend(f"• {item['name']}" for item in canteens)
            output.append("\nAsk about CEC Canteen, Can Cafe or Can Express.")
            return "\n".join(output)

        if selected.get("details_status"):
            return (f"{selected['name']}: {selected['details_status']}. "
                    "Please share its timings, menu, prices or contact details so I can add them.")

        output = [f"{selected['name']} Details:"]
        output.append(f"Days: {selected['days_open']}")
        output.append(f"Timings: {selected['opening_time']} – {selected['closing_time']}")
        output.append("Offerings: " + ", ".join(selected["offerings"]))
        output.append(f"Approximate price range: {selected['approximate_price_range']}")
        output.append(f"\nNote: {selected['source_note']}")
        return "\n".join(output)


    def _library_answer(self, message):
        q = message.lower()
        library_terms = ["library", "librarian", "book bank", "digital library", "reading section", "reference section", "circulation section", "journals", "e-books", "e-journals"]
        if not any(term in q for term in library_terms):
            return None

        if any(term in q for term in ["staff", "librarian", "library assistant", "library asst", "office assistant", "office asst", "who works"]):
            people = self.library_data.get("staff", [])
            output = ["Central Library – Staff:"]
            output.extend(f"• {person['name']} — {person['designation']}" for person in people)
            output.append("\n" + self.library_data.get("staff_source_note", "Contact details are not available in the current knowledge base."))
            return "\n".join(output)

        sections = self.library_data["sections"]
        if any(term in q for term in ["all facilities", "library facilities", "library sections", "all sections", "library details", "central library"]):
            output = [f"{self.library_data['name']} – Sections and Facilities", "Users: " + ", ".join(self.library_data["users"])]
            for section in sections:
                output.append(f"\n{section['name']}:")
                facilities = section.get("facilities", {})
                if facilities:
                    labels = {
                        "books": "Books", "bound_volumes": "Bound Volumes", "national_journals": "National Journals",
                        "magazines": "Magazines", "newspapers": "Newspapers", "seating_capacity": "Seating Capacity",
                        "pcs": "PCs", "book_stacking": "Book Stacking", "extended_lan_docking_facility": "Extended LAN Docking Facility",
                        "resources": "Resources", "other_resources": "Other Resources"
                    }
                    for key, value in facilities.items():
                        output.append(f"• {labels.get(key, key.replace('_', ' ').title())}: {', '.join(map(str, value)) if isinstance(value, list) else value}")
                output.append(f"• Working Hours: {section['working_hours']}")
            output.append("\nSource note: " + self.library_data["source_note"])
            return "\n".join(output)

        if any(term in q for term in ["timing", "time", "hours", "open", "working hour"]):
            if "reference" in q:
                selected = [sections[0]]
            elif "circulation" in q:
                selected = [sections[1]]
            elif "digital" in q:
                selected = [sections[2]]
            elif "sc/st" in q or "sc st" in q:
                selected = [sections[3]]
            elif "general book" in q:
                selected = [sections[4]]
            elif "reading" in q:
                selected = [sections[5]]
            else:
                selected = sections
            output = ["Library Working Hours:"]
            output.extend(f"• {section['name']}: {section['working_hours']}" for section in selected)
            output.append("\nNote: " + self.library_data["source_note"])
            return "\n".join(output)

        selected = None
        for section in sections:
            if section["name"].lower() in q or (section["name"].replace(" Section", "").lower() in q):
                selected = section
                break
        if selected:
            output = [f"{selected['name']}:"]
            facilities = selected.get("facilities", {})
            if facilities:
                for key, value in facilities.items():
                    label = key.replace("_", " ").title()
                    output.append(f"• {label}: {', '.join(map(str, value)) if isinstance(value, list) else value}")
            output.append(f"• Working Hours: {selected['working_hours']}")
            output.append("\nSource note: " + self.library_data["source_note"])
            return "\n".join(output)

        return ("The Central Library has Reference, Circulation, Digital Library, SC/ST Book Bank, "
                "General Book Bank and Reading sections. Ask about a section, its facilities or working hours.\n\n"
                + self.library_data["source_note"])


    def _college_hours_answer(self, message):
        q = message.lower()
        timing_terms = ["college timing", "college timings", "college hours", "office timing", "office timings",
                        "office hours", "working hours", "working time", "college open", "college close",
                        "sports timing", "sports hours", "sports facilities", "facility timing",
                        "facilities after college", "after college", "late training", "training transport"]
        if not any(term in q for term in timing_terms):
            return None

        info = self.college_info
        if any(term in q for term in ["sports", "facility", "training", "late", "after college"]):
            output = ["Sports and Campus Facility Access:",
                      f"• Access: Until {info['sports_facility_timing'].split('until ', 1)[-1] if 'until ' in info['sports_facility_timing'] else info['sports_facility_timing']}",
                      f"• Late-training transport: {info['late_training_transport']}"]
        else:
            output = [f"{info['college_name']} – College/Office Timings:",
                      f"• Working days: {info['working_days']}",
                      f"• Typical office hours: {info['office_timing']}",
                      f"• Sports and campus facilities: {info['sports_facility_timing']}",
                      f"• Late-training transport: {info['late_training_transport']}"]
        output.append("\nNote: " + info['source_note'])
        return "\n".join(output)

    def _holiday_answer(self, message):
        q = message.lower()
        terms = ["holiday", "holidays", "public holiday", "government holiday", "govt holiday", "holiday list"]
        if not any(term in q for term in terms):
            return None
        year = "2027" if "2027" in q else "2026"
        if year == "2027":
            return ("Karnataka Government holiday dates for 2027 have not been added because an official "
                    "2027 notification was not available in the sources checked as of 15 November 2026. "
                    "Please check the latest government notification and the college circular.")
        data = self.holiday_data
        output = [f"Karnataka Government General Holidays – {data['year']}:"]
        output.extend(f"• {item['date']} ({item['day']}) – {item['name']}" for item in data["general_holidays"])
        output.append("\nWeekly closures: " + data["weekly_closures"])
        output.append("\nNote: " + data["source_note"])
        return "\n".join(output)

    def _academic_calendar_answer(self, message):
        q = message.lower()
        calendar_terms = ["academic calendar", "semester calendar", "semester dates", "commencement of classes",
                          "last working day", "exam dates", "examination dates", "exam schedule",
                          "odd semester", "even semester", "v/vii", "vi/viii", "summer semester"]
        if not any(term in q for term in calendar_terms):
            return None

        odd = self.academic_calendar["odd_semester"]
        even = self.academic_calendar["even_semester"]
        if any(term in q for term in ["odd", "v/vii", "5th", "5th semester", "7th", "7th semester"]):
            data = odd
            output = [f"Odd Semester Academic Calendar – {data['semester']} (2025–26):",
                      f"• Pre-semester preparations: {data['pre_semester_preparations']}",
                      "• Activities: " + ", ".join(data["pre_semester_activities"]),
                      f"• Commencement of classes: {data['commencement_of_classes']}",
                      f"• Last working day: {data['last_working_day']}",
                      f"• Theory and practical examinations: {data['examinations']}",
                      f"• {data['next_semester']} commencement: {data['next_semester_commencement']}"]
        elif any(term in q for term in ["even", "2026", "summer semester"]):
            data = even
            output = ["Even Semester Academic Calendar (2026):",
                      f"• Commencement of classes: {data['commencement_of_classes']}",
                      f"• Last working day: {data['last_working_day']}",
                      f"• Practical and theory examinations: {data['examinations']}",
                      f"• Summer semester commencement: {data['summer_semester_commencement']}"]
        else:
            output = ["Canara Engineering College – Academic Calendar 2025–26",
                      "\nOdd Semester – V/VII Semester B.E.:",
                      f"• Pre-semester preparations: {odd['pre_semester_preparations']}",
                      f"• Classes commence: {odd['commencement_of_classes']}",
                      f"• Last working day: {odd['last_working_day']}",
                      f"• Examinations: {odd['examinations']}",
                      f"• VI/VIII Semester commences: {odd['next_semester_commencement']}",
                      "\nEven Semester (2026):",
                      f"• Classes commence: {even['commencement_of_classes']}",
                      f"• Last working day: {even['last_working_day']}",
                      f"• Examinations: {even['examinations']}",
                      f"• Summer semester commences: {even['summer_semester_commencement']}"]
        output.append("\nSource note: " + self.academic_calendar["source_note"])
        return "\n".join(output)


    def _fee_answer(self, message):
        q = message.lower()
        fee_terms = ["fee", "fees", "fee structure", "tuition", "cost", "charges",
                     "hostel fee", "hostel fees", "bus fee", "bus fees", "transport fee",
                     "transportation fee", "skill lab", "scholarship", "scholarships"]
        if not any(term in q for term in fee_terms):
            return None

        data = self.fee_data
        if any(term in q for term in ["scholarship", "scholarships"]):
            return ("Scholarship details have not been provided in CampusMate. "
                    "For updated scholarship information, eligibility and application instructions, "
                    "please visit the official Canara Engineering College website: https://www.cec.edu.in/ "
                    "You can also check the college admission page: https://cec.edu.in/admission. "
                    "Please refer to the latest college and government notifications.")

        if any(term in q for term in ["hostel fee", "hostel fees", "hostel charge", "hostel charges"]):
            hostel = data["hostel_fees"]
            return ("Hostel Fees (approximate, per year):\n"
                    f"• Double room (common bath): {hostel['double_common_bath']}\n"
                    f"• Double room (attached bath): {hostel['double_attached_bath']}\n"
                    f"Note: {data['source_note']}")

        if any(term in q for term in ["bus fee", "bus fees", "transport fee", "transportation fee", "transport charges"]):
            transport = data["transport_fees"]
            return ("Bus / Transportation Fees (annual, approximate):\n"
                    f"• Range: {transport['annual_range']}\n"
                    f"• Route examples supplied: {transport['route_examples']}\n"
                    f"Note: {transport['note']} {data['source_note']}")

        if any(term in q for term in ["kcet", "government quota", "govt quota"]):
            item = data["engineering_fees"]["kcet_government_quota"]
            label = "KCET / Government Quota"
        elif any(term in q for term in ["krlmpca", "comedk", "minority quota"]):
            item = data["engineering_fees"]["krlmpca_minority_comedk_quota"]
            label = "KRLMPCA / Minority / COMEDK Quota"
        elif "management" in q:
            item = data["engineering_fees"]["management_quota"]
            label = "Management Quota"
        else:
            output = ["B.E. / B.Tech Fee Information (approximate):"]
            for key, item in data["engineering_fees"].items():
                output.append(f"\n{item['label']}:")
                output.append(f"• Annual tuition and university fees: {item['annual_range']}")
                if item.get("four_year_total"):
                    output.append(f"• Approximate four-year total: {item['four_year_total']}")
                if item.get("breakdown"):
                    output.append(f"• Breakdown: {item['breakdown']}")
            other = data["additional_annual_fees"]
            output.extend(["\nAdditional Annual Fees:",
                           f"• Nominal / other college fees: {other['nominal_other_fees']}",
                           f"• Skill lab expenses: {other['skill_lab_expenses']}",
                           "\nAsk about KCET, COMEDK/KRLMPCA, management, hostel or bus fees for more specific details.",
                           "\nNote: " + data["source_note"]])
            return "\n".join(output)

        output = [f"{label}:", f"• Annual tuition and university fees: {item['annual_range']}"]
        if item.get("breakdown"):
            output.append(f"• Approximate breakdown: {item['breakdown']}")
        if item.get("four_year_total"):
            output.append(f"• Approximate four-year total: {item['four_year_total']}")
        output.append("\nAdditional annual charges may apply:")
        output.append(f"• Nominal / other college fees: {data['additional_annual_fees']['nominal_other_fees']}")
        output.append(f"• Skill lab expenses: {data['additional_annual_fees']['skill_lab_expenses']}")
        output.append("\nNote: " + data["source_note"])
        return "\n".join(output)

    def _admission_answer(self, message):
        q = message.lower()
        terms = ["admission", "eligibility", "eligible", "entrance exam", "entrance test",
                 "kcet", "comedk", "krlmpca", "jee main", "required documents",
                 "documents required", "documents for admission", "how to apply",
                 "apply for be", "apply for b.e", "pcm aggregate", "minimum marks"]
        if not any(term in q for term in terms):
            return None

        data = self.admission_data
        if any(term in q for term in ["document", "certificate", "what to submit"]):
            output = ["B.E. / B.Tech Admission – Required Documents:"]
            output.extend(f"• {item}" for item in data["required_documents"])
            output.append("\nPlease confirm the current year's document checklist with the college/admission authority.")
            output.append(f"Official admission page: {data['official_admission_url']}")
            return "\n".join(output)

        if any(term in q for term in ["entrance exam", "entrance test", "kcet", "comedk", "krlmpca", "jee main"]):
            output = ["Accepted entrance examinations for B.E. / B.Tech (as supplied):"]
            output.extend(f"• {item['name']} — {item['details']}" for item in data["accepted_entrance_exams"])
            output.append("\nFor current-year exam and counselling rules, check the official admission page.")
            output.append(f"{data['official_admission_url']}")
            return "\n".join(output)

        if any(term in q for term in ["process", "how to apply", "application", "quota", "government quota", "management quota"]):
            output = ["B.E. / B.Tech Admission Process:"]
            for route in data["admission_routes"]:
                line = f"\n{route['quota']}"
                if route.get("seat_share"):
                    line += f" ({route['seat_share']})"
                output.append(line + ": " + route["process"])
            output.append("\nOfficial admission page: " + data["official_admission_url"])
            output.append("Note: " + data["source_note"])
            return "\n".join(output)

        output = ["B.E. / B.Tech Eligibility Criteria:",
                  f"• Academic qualification: {data['academic_qualification']}",
                  f"• Compulsory subjects: {data['compulsory_subjects']}",
                  f"• General category: {data['minimum_marks']['general']}",
                  f"• Reserved categories: {data['minimum_marks']['reserved']}",
                  "\nAccepted entrance exams: KCET, COMEDK UGET, JEE Main and KRLMPCA UGCET.",
                  "\nFor the admission process, required documents and current-year updates, visit: " + data["official_admission_url"],
                  "\nNote: " + data["source_note"]]
        return "\n".join(output)

    def _events_answer(self, message):
        q = message.lower()
        event_terms = ["event", "events", "fest", "aakriti", "akrithi", "hackathon", "innovation league",
                       "technovation", "project exhibition", "project expo", "freshers", "desiverse",
                       "induction programme", "induction program", "iot innovatex"]
        if not any(term in q for term in event_terms):
            return None

        data = self.events_data
        if any(term in q for term in ["instagram", "event page", "event updates", "upcoming"]):
            return ("For current and upcoming college event announcements, visit the CEC Events Instagram page:\n"
                    f"{data['events_instagram']}\nCollege website: {data['college_website']}\n\n"
                    + data["source_note"])

        if (any(term in q for term in ["aakriti", "akrithi", "main event", "main fest", "annual fest"])
                or ("main" in q and "college" in q and "fest" in q)):
            item = data["main_annual_event"]
            return (f"{item['name']} – {item['description']}\n"
                    f"• Dates: {item['dates']}\n• Phases: {item['phases']}\n"
                    f"• Website: {item['website']}\n\nNote: {data['source_note']}")

        query_words = set(re.findall(r"[a-z0-9]+", q))
        for item in data["events"]:
            name_words = [word for word in re.findall(r"[a-z0-9]+", item["name"].lower()) if len(word) > 3 and not word.isdigit()]
            if query_words.intersection(name_words):
                return (f"{item['name']}\n• Date: {item['date']}\n• Category: {item['category']}\n\n"
                        f"For current event updates, visit: {data['events_instagram']}\n"
                        f"Note: {data['source_note']}")

        output = ["Canara Engineering College – Events (2026):"]
        for item in data["events"]:
            output.append(f"• {item['name']} — {item['date']}")
        main = data["main_annual_event"]
        output.extend([f"• {main['name']} ({main['description']}) — {main['dates']}",
                       "\nFor current and upcoming announcements, visit: " + data["events_instagram"],
                       "College website: " + data["college_website"],
                       "\nNote: " + data["source_note"]])
        return "\n".join(output)

    def _small_talk_answer(self, message):
        q = re.sub(r"[^a-z0-9\s]", "", message.lower()).strip()
        greetings = {"hi", "hii", "hiii", "hello", "hey", "heyy", "good morning", "good afternoon", "good evening"}
        if q in greetings or q.startswith(("hi ", "hello ", "hey ")):
            if "morning" in q:
                return "Good morning! ☀️ Welcome to CampusMate. What would you like to know about your college today?"
            if "afternoon" in q:
                return "Good afternoon! 😊 I'm here to help with college information. What can I help you with?"
            if "evening" in q:
                return "Good evening! 🌙 Welcome back to CampusMate. How can I help you?"
            return "Hi there! 👋 Welcome to CampusMate! I'm your AI College Assistant. How are you today?"
        if q in {"how are you", "how are you doing", "hru", "how r u", "how r u doing"} or q.startswith(("how r u", "how are u", "how are you")):
            return "I'm doing great, thank you for asking! 🤖 I'm ready to help you with college-related questions. How can I help you?"
        if q in {"im good", "i am good", "im fine", "i am fine", "good", "fine", "great"}:
            return "Glad to hear that! 😊 What would you like to explore today—departments, hostel, buses, library, admissions or something else?"
        if q in {"who are you", "what are you", "what is campusmate", "introduce yourself"}:
            return "I'm CampusMate, your AI College Assistant for Canara Engineering College. 🎓 I can help you find college information and answer questions using the information available in my knowledge base."
        if q in {"what can you do", "how can you help me", "how can you help", "help me"}:
            return ("I can help you with these college topics:\n"
                    "• Departments, HODs and faculty\n• Hostel facilities, rules and wardens\n"
                    "• Bus routes, stops and coordinators\n• Canteens\n• Library facilities and staff\n"
                    "• College timings, events and holidays\n• Academic calendar\n"
                    "• Fees, scholarships and admissions\n\nWhat would you like to know?")
        if q in {"thank you", "thanks", "thank u", "thx"}:
            return "You're most welcome! 💜 I'm happy to help. Feel free to ask me anything about the college."
        if q in {"bye", "goodbye", "see you", "see ya"}:
            return "Goodbye! 👋 Have a lovely day, and come back whenever you need college information."
        if q in {"what are you doing", "wyd"}:
            return "I'm right here, ready to help students with college-related questions! 🤖"
        return None

    def get_response(self, message):
        small_talk_answer = self._small_talk_answer(message)
        if small_talk_answer:
            return small_talk_answer
        events_answer = self._events_answer(message)
        if events_answer:
            return events_answer
        fee_answer = self._fee_answer(message)
        if fee_answer:
            return fee_answer
        admission_answer = self._admission_answer(message)
        if admission_answer:
            return admission_answer
        holiday_answer = self._holiday_answer(message)
        if holiday_answer:
            return holiday_answer
        academic_calendar_answer = self._academic_calendar_answer(message)
        if academic_calendar_answer:
            return academic_calendar_answer
        college_hours_answer = self._college_hours_answer(message)
        if college_hours_answer:
            return college_hours_answer
        library_answer = self._library_answer(message)
        if library_answer:
            return library_answer
        canteen_answer = self._canteen_answer(message)
        if canteen_answer:
            return canteen_answer
        bus_answer = self._bus_answer(message)
        if bus_answer:
            return bus_answer
        hostel_answer = self._hostel_answer(message)
        if hostel_answer:
            return hostel_answer
        dept_answer = self._department_answer(message)
        if dept_answer:
            return dept_answer
        if self.matrix is not None:
            vector = self.vectorizer.transform([message])
            scores = cosine_similarity(vector, self.matrix).flatten()
            best = scores.argmax()
            if scores[best] >= 0.24:
                return self.answers[best]
        return ("I don't have verified information for that question in my current knowledge base. "
                "You can ask about departments and faculty, hostel rules and wardens, bus routes, canteens, "
                "library facilities and staff, college timings, events, holidays, the academic calendar, "
                "fees, scholarships or B.E. / B.Tech admissions. I won't guess or provide unverified details.")
