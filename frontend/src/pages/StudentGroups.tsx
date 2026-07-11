import { useEffect, useState } from 'react';
import StudentLayout from '@/components/StudentLayout';
import api from '@/lib/api';
import { 
  Users, 
  BookOpen, 
  Calendar, 
  Plus, 
  X, 
  CheckSquare, 
  Clock, 
  MapPin, 
  FileText,
  DoorOpen
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/Toast';

export default function StudentGroups() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [activeTab, setActiveTab] = useState<'my-groups' | 'explore'>('my-groups');
  const [joinedGroups, setJoinedGroups] = useState<any[]>([]);
  const [exploreGroups, setExploreGroups] = useState<any[]>([]);
  
  // Selected classroom state
  const [selectedGroup, setSelectedGroup] = useState<any | null>(null);
  const [groupMembers, setGroupMembers] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);

  // Modal creation state
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [showAddAssignmentModal, setShowAddAssignmentModal] = useState(false);
  const [showAddEventModal, setShowAddEventModal] = useState(false);

  // Form fields
  const [groupName, setGroupName] = useState('');
  const [groupDesc, setGroupDesc] = useState('');
  const [isClassroom, setIsClassroom] = useState(false);
  const [groupDept, setGroupDept] = useState('');
  const [creatingGroup, setCreatingGroup] = useState(false);

  // Assignment fields
  const [assignTitle, setAssignTitle] = useState('');
  const [assignDesc, setAssignDesc] = useState('');
  const [assignDue, setAssignDue] = useState('');
  const [submittingAssign, setSubmittingAssign] = useState(false);

  // Event fields
  const [eventTitle, setEventTitle] = useState('');
  const [eventDesc, setEventDesc] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [eventLoc, setEventLoc] = useState('');
  const [submittingEvent, setSubmittingEvent] = useState(false);

  const loadGroupsData = async () => {
    try {
      // 1. Get joined groups
      const joined = await api.getGroups(true);
      setJoinedGroups(joined);

      // 2. Get public explore groups
      const allPublic = await api.getGroups(false);
      const joinedIds = joined.map(j => j.id);
      const filteredExplore = allPublic.filter(g => !joinedIds.includes(g.id));
      setExploreGroups(filteredExplore);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadGroupsData();
  }, []);

  const handleSelectGroup = async (group: any) => {
    setSelectedGroup(group);
    try {
      const members = await api.getGroupMembers(group.id);
      setGroupMembers(members);
      const assignList = await api.getAssignments(group.id);
      setAssignments(assignList);
      const eventList = await api.getEvents(group.id);
      setEvents(eventList);
    } catch (err) {
      console.error(err);
    }
  };

  const handleJoinGroup = async (groupId: number) => {
    try {
      await api.joinGroup(groupId);
      showToast('Joined group successfully!', 'success');
      loadGroupsData();
    } catch (err) {
      showToast('Failed to join group.', 'error');
    }
  };

  const handleLeaveGroup = async (groupId: number) => {
    try {
      await api.leaveGroup(groupId);
      showToast('Left group', 'success');
      setSelectedGroup(null);
      loadGroupsData();
    } catch (err) {
      showToast('Failed to leave group.', 'error');
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupName.trim()) return;
    setCreatingGroup(true);
    try {
      const newGroup = await api.createGroup({
        name: groupName,
        description: groupDesc,
        is_classroom: isClassroom,
        class_or_department: groupDept
      });
      showToast('Group created successfully!', 'success');
      setGroupName('');
      setGroupDesc('');
      setIsClassroom(false);
      setGroupDept('');
      setShowCreateGroupModal(false);
      loadGroupsData();
      handleSelectGroup(newGroup);
    } catch (err) {
      showToast('Failed to create group.', 'error');
    } finally {
      setCreatingGroup(false);
    }
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assignTitle.trim() || !selectedGroup) return;
    setSubmittingAssign(true);
    try {
      await api.createAssignment(selectedGroup.id, {
        title: assignTitle,
        description: assignDesc,
        due_date: assignDue
      });
      showToast('Assignment added!', 'success');
      setAssignTitle('');
      setAssignDesc('');
      setAssignDue('');
      setShowAddAssignmentModal(false);
      
      // Reload details
      const assignList = await api.getAssignments(selectedGroup.id);
      setAssignments(assignList);
    } catch (err) {
      showToast('Failed to add assignment.', 'error');
    } finally {
      setSubmittingAssign(false);
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!eventTitle.trim() || !selectedGroup) return;
    setSubmittingEvent(true);
    try {
      await api.createEvent(selectedGroup.id, {
        title: eventTitle,
        description: eventDesc,
        date: eventDate,
        location: eventLoc
      });
      showToast('Event added!', 'success');
      setEventTitle('');
      setEventDesc('');
      setEventDate('');
      setEventLoc('');
      setShowAddEventModal(false);
      
      // Reload details
      const eventList = await api.getEvents(selectedGroup.id);
      setEvents(eventList);
    } catch (err) {
      showToast('Failed to add event.', 'error');
    } finally {
      setSubmittingEvent(false);
    }
  };

  return (
    <StudentLayout>
      <div className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Groups list */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
            
            {/* Header controls */}
            <div className="flex justify-between items-center">
              <h2 className="font-extrabold text-base flex items-center gap-2">
                <Users className="h-5 w-5 text-indigo-500" />
                Groups
              </h2>
              <button
                onClick={() => setShowCreateGroupModal(true)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg p-1.5 transition"
              >
                <Plus className="h-4.5 w-4.5" />
              </button>
            </div>

            {/* Toggle tabs */}
            <div className="grid grid-cols-2 bg-slate-100 dark:bg-slate-950 p-1 rounded-xl border border-slate-200/40 dark:border-slate-850">
              <button
                onClick={() => setActiveTab('my-groups')}
                className={`py-1.5 text-xs font-semibold rounded-lg transition ${
                  activeTab === 'my-groups' ? 'bg-white dark:bg-slate-900 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-slate-400'
                }`}
              >
                My Groups
              </button>
              <button
                onClick={() => setActiveTab('explore')}
                className={`py-1.5 text-xs font-semibold rounded-lg transition ${
                  activeTab === 'explore' ? 'bg-white dark:bg-slate-900 shadow-sm text-indigo-600 dark:text-indigo-400' : 'text-slate-400'
                }`}
              >
                Explore
              </button>
            </div>

            {/* Groups list render */}
            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
              {activeTab === 'my-groups' ? (
                joinedGroups.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-6 italic">You haven't joined any groups yet.</p>
                ) : (
                  joinedGroups.map(g => (
                    <div
                      key={g.id}
                      onClick={() => handleSelectGroup(g)}
                      className={`p-3 rounded-xl cursor-pointer border transition ${
                        selectedGroup?.id === g.id 
                          ? 'bg-indigo-50 dark:bg-indigo-950/30 border-indigo-200 dark:border-indigo-900/60' 
                          : 'bg-slate-50/50 dark:bg-slate-900/40 border-slate-100 dark:border-slate-850 hover:bg-slate-50 dark:hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <h4 className="font-bold text-xs">{g.name}</h4>
                        <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded-full uppercase ${
                          g.is_classroom ? 'bg-blue-100 dark:bg-blue-950 text-blue-600' : 'bg-green-100 dark:bg-green-950 text-green-600'
                        }`}>
                          {g.is_classroom ? 'Classroom' : 'Club'}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-1 line-clamp-2">{g.description}</p>
                    </div>
                  ))
                )
              ) : (
                exploreGroups.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-6 italic">No new groups to explore.</p>
                ) : (
                  exploreGroups.map(g => (
                    <div
                      key={g.id}
                      className="p-3 bg-slate-50/50 dark:bg-slate-900/40 border border-slate-100 dark:border-slate-850 rounded-xl space-y-2"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-bold text-xs">{g.name}</h4>
                          <p className="text-[9px] text-slate-400 dark:text-slate-500 font-semibold">{g.class_or_department || 'General'}</p>
                        </div>
                        <button
                          onClick={() => handleJoinGroup(g.id)}
                          className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[9px] px-2.5 py-1.5 rounded-lg transition"
                        >
                          Join
                        </button>
                      </div>
                      <p className="text-[10px] text-slate-400 line-clamp-2">{g.description}</p>
                    </div>
                  ))
                )
              )}
            </div>

          </div>
        </div>

        {/* Right Side: Group Detail panel */}
        <div className="lg:col-span-2 space-y-6">
          {selectedGroup ? (
            <div className="space-y-6">
              
              {/* Group Hero Info */}
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="font-extrabold text-xl">{selectedGroup.name}</h2>
                    <p className="text-xs font-semibold text-indigo-500 dark:text-indigo-400 mt-1">
                      {selectedGroup.class_or_department || 'General Study Group'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleLeaveGroup(selectedGroup.id)}
                    className="flex items-center gap-1.5 bg-rose-50 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 hover:bg-rose-100 font-bold text-[10px] px-3.5 py-2 rounded-xl transition"
                  >
                    <DoorOpen className="h-4 w-4" />
                    Leave Group
                  </button>
                </div>
                <p className="text-sm text-slate-655 dark:text-slate-300 leading-relaxed">
                  {selectedGroup.description}
                </p>

                {/* Member avatars */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-3">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Members:</span>
                  <div className="flex -space-x-2.5 overflow-hidden">
                    {groupMembers.map(m => (
                      <img
                        key={m.id}
                        src={m.profile_pic_url || `https://api.dicebear.com/7.x/adventurer/svg?seed=${m.username}`}
                        title={`@${m.username}`}
                        className="inline-block h-7 w-7 rounded-full ring-2 ring-white dark:ring-slate-900 bg-slate-100 dark:bg-slate-800"
                      />
                    ))}
                  </div>
                  <span className="text-xs font-bold text-slate-500">({groupMembers.length})</span>
                </div>
              </div>

              {/* Classroom Tabbed details: Assignments & Events */}
              {selectedGroup.is_classroom ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Classroom Assignments */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="font-extrabold text-sm flex items-center gap-2">
                        <CheckSquare className="h-4.5 w-4.5 text-indigo-500" />
                        Assignments
                      </h3>
                      <button
                        onClick={() => setShowAddAssignmentModal(true)}
                        className="bg-indigo-650/10 hover:bg-indigo-650/20 text-indigo-500 rounded-lg p-1 transition"
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="space-y-3 max-h-[45vh] overflow-y-auto pr-1">
                      {assignments.length === 0 ? (
                        <p className="text-xs text-slate-400 italic text-center py-10">No active assignments posted.</p>
                      ) : (
                        assignments.map((ass) => (
                          <div key={ass.id} className="p-3 bg-slate-50/50 dark:bg-slate-950 rounded-2xl border border-slate-150 dark:border-slate-850 space-y-2">
                            <div className="flex justify-between items-start">
                              <h4 className="font-bold text-xs">{ass.title}</h4>
                              {ass.due_date && (
                                <span className="text-[9px] bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400 font-bold px-1.5 py-0.5 rounded-md flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  Due: {new Date(ass.due_date).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 leading-normal">{ass.description}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Classroom Events */}
                  <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-5 shadow-sm space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="font-extrabold text-sm flex items-center gap-2">
                        <Calendar className="h-4.5 w-4.5 text-indigo-500" />
                        Class Calendar
                      </h3>
                      <button
                        onClick={() => setShowAddEventModal(true)}
                        className="bg-indigo-650/10 hover:bg-indigo-650/20 text-indigo-500 rounded-lg p-1 transition"
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="space-y-3 max-h-[45vh] overflow-y-auto pr-1">
                      {events.length === 0 ? (
                        <p className="text-xs text-slate-400 italic text-center py-10">No upcoming events scheduled.</p>
                      ) : (
                        events.map((ev) => (
                          <div key={ev.id} className="p-3 bg-slate-50/50 dark:bg-slate-950 rounded-2xl border border-slate-150 dark:border-slate-850 space-y-2">
                            <div className="flex justify-between items-start">
                              <h4 className="font-bold text-xs">{ev.title}</h4>
                              <span className="text-[9px] bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 font-bold px-1.5 py-0.5 rounded-md">
                                {new Date(ev.date).toLocaleDateString()}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-normal">{ev.description}</p>
                            {ev.location && (
                              <p className="text-[9px] text-indigo-500 dark:text-indigo-400 font-semibold flex items-center gap-1">
                                <MapPin className="h-3 w-3" />
                                {ev.location}
                              </p>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                </div>
              ) : (
                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 text-center text-slate-400">
                  <Users className="h-10 w-10 mx-auto mb-3 opacity-30 text-indigo-500" />
                  <p className="font-bold text-sm">Welcome to study/club room!</p>
                  <p className="text-xs mt-1">Discuss assignments, schedule study dates, and share materials.</p>
                </div>
              )}

            </div>
          ) : (
            <div className="h-[60vh] flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-sm">
              <BookOpen className="h-12 w-12 opacity-30 text-indigo-500 mb-3" />
              <p className="font-bold text-sm">No Group Selected</p>
              <p className="text-xs mt-1">Select a group or classroom from the sidebar list to see details.</p>
            </div>
          )}
        </div>

      </div>

      {/* Create Group Modal */}
      {showCreateGroupModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-5 shadow-2xl relative">
            <button 
              onClick={() => setShowCreateGroupModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="h-5 w-5" />
            </button>
            <h3 className="font-bold text-base mb-4">Create Study Group</h3>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Group Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Physics Study Circle"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Description</label>
                <textarea
                  placeholder="What is this group about?"
                  rows={3}
                  value={groupDesc}
                  onChange={(e) => setGroupDesc(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white resize-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Department / Class</label>
                <input
                  type="text"
                  placeholder="e.g. Science Dept"
                  value={groupDept}
                  onChange={(e) => setGroupDept(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-855 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-855 dark:text-white"
                />
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="is_classroom_box"
                  checked={isClassroom}
                  onChange={(e) => setIsClassroom(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="is_classroom_box" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Register as formal Classroom (Enables assignments / events)
                </label>
              </div>
              <button
                type="submit"
                disabled={creatingGroup || !groupName.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition"
              >
                {creatingGroup ? 'Creating...' : 'Create Group'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Add Assignment Modal */}
      {showAddAssignmentModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-5 shadow-2xl relative">
            <button 
              onClick={() => setShowAddAssignmentModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="h-5 w-5" />
            </button>
            <h3 className="font-bold text-base mb-4">Post Assignment</h3>
            <form onSubmit={handleCreateAssignment} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Lab Report 1"
                  value={assignTitle}
                  onChange={(e) => setAssignTitle(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Description</label>
                <textarea
                  placeholder="Details of the assignment..."
                  rows={3}
                  value={assignDesc}
                  onChange={(e) => setAssignDesc(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white resize-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Due Date</label>
                <input
                  type="date"
                  value={assignDue}
                  onChange={(e) => setAssignDue(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white"
                />
              </div>
              <button
                type="submit"
                disabled={submittingAssign || !assignTitle.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition"
              >
                {submittingAssign ? 'Adding...' : 'Post Assignment'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Add Event Modal */}
      {showAddEventModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-sm w-full p-5 shadow-2xl relative">
            <button 
              onClick={() => setShowAddEventModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
            >
              <X className="h-5 w-5" />
            </button>
            <h3 className="font-bold text-base mb-4">Add Class Event</h3>
            <form onSubmit={handleCreateEvent} className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Event Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Midterm Review"
                  value={eventTitle}
                  onChange={(e) => setEventTitle(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Description</label>
                <textarea
                  placeholder="Event details..."
                  rows={3}
                  value={eventDesc}
                  onChange={(e) => setEventDesc(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white resize-none"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Event Date *</label>
                <input
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-500">Location</label>
                <input
                  type="text"
                  placeholder="e.g. Room 204B"
                  value={eventLoc}
                  onChange={(e) => setEventLoc(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-850 px-3 py-2 rounded-xl text-xs focus:outline-none text-slate-850 dark:text-white"
                />
              </div>
              <button
                type="submit"
                disabled={submittingEvent || !eventTitle.trim()}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2.5 rounded-xl transition"
              >
                {submittingEvent ? 'Adding...' : 'Schedule Event'}
              </button>
            </form>
          </div>
        </div>
      )}

    </StudentLayout>
  );
}
