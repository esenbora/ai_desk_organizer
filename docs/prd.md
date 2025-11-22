# **Product Requirements Document (PRD)**

| Project Name | DeskOpt |
| :---- | :---- |
| **Version** | 1.1 (Desktop Pivot) |
| **Status** | Ready for Dev |
| **Author** | Nazik |

## **1\. Problem Statement**

* **The Pain:** Disorganized workspaces cause physical strain and cognitive load.  
* **The Failure:** Generic advice fails because it lacks context of the user's hardware and workflow.  
* **The Solution:** An AI Ergonomics Engine that audits the user's inventory and generates a role-specific spatial layout.

## **2\. Target Audience**

* **Primary:** High-Intensity Desk Users (Devs, Editors, Traders).  
* **Secondary:** Students/Researchers with mixed media.

## **3\. Functional Requirements (MVP)**

### **3.1 Input & Context**

| ID | Feature Name | User Story | Acceptance Criteria |
| :---- | :---- | :---- | :---- |
| **F-01** | **Manual Calibration** | As a user, I click the corners of my reference object (Card) to calibrate scale. | \- User clicks 4 points on the image. \- System computes pixel-to-cm ratio. |
| **F-02** | **Role & Handedness** | As a user, I define my ergonomic profile. | \- Dropdown: Left/Right hand. \- Dropdown Role: Coder, Artist, Admin. |

### **3.2 The "Triage" Loop (Critical Path)**

| ID | Feature Name | User Story | Acceptance Criteria |
| :---- | :---- | :---- | :---- |
| **F-03** | **Inventory Audit** | As a user, I correct the AI's labels before getting advice. | \- **Table View:** Display detected items. \- **Edit:** Rename/Delete/Exclude items. |

### **3.3 Output**

| ID | Feature Name | User Story | Acceptance Criteria |
| :---- | :---- | :---- | :---- |
| **F-04** | **Ghost Overlay** | As a user, I see exactly where to move items on my monitor. | \- Render colored boxes on the image. \- Green Arrow: Optimal move. \- Red Zone: Warning. |
| **F-05** | **Schematic Blueprint** | As a user, I want a clean map. | \- Top-down 2D grid view rendered in a separate window or tab. |

## **4\. User Experience (UX) Flow**

1. **Import:** User drags a photo (taken via phone) into the Desktop App.  
2. **Calibrate:** User clicks 4 corners of the credit card visible in the photo.  
3. **Context:** User selects "Right-Handed Coder."  
4. **Processing:** AI analyzes inventory.  
5. **Triage:** User reviews the item list.  
6. **Result:** App displays the ergonomic overlay.

## **5\. Technical Constraints**

* **File Transfer:** The app assumes the user has already transferred the photo to their computer.  
* **Platform:** Windows/macOS (Python-based).

## **6\. Success Metrics**

* **Completion Rate:** Users who reach the final result screen despite the file transfer friction.