export const mockBranches = [
  { id: 1, name: 'Liebhaus Gurukula', location: 'Kidangoor', username: 'liebhaus', password: 'Liebhaus@2026', tag: 'Design & Mentoring' },
  { id: 2, name: 'Bethsleeha Gurukula', location: 'Kaduthuruthy', username: 'bethsleeha', password: 'Bethsleeha@2026', tag: 'Value Education' },
  { id: 3, name: 'Pala Gurukula', location: 'Pala', username: 'pala_gurukula', password: 'PalaGurukula@2026', tag: 'Science & Discipline' },
  { id: 4, name: 'Greccio Gurukula', location: 'Kizhaparayar', username: 'greccio', password: 'Greccio@2026', tag: 'Eco & Spiritual' },
  { id: 5, name: 'St.Alphonsa Gurukula', location: 'Bharanaganam', username: 'stalphonsa', password: 'StAlphonsa@2026', tag: 'Scholarship & Service' },
  { id: 6, name: 'Traumhaus Gurukula', location: 'Bharanaganam', username: 'traumhaus', password: 'Traumhaus@2026', tag: 'Creative Arts' },
  { id: 7, name: 'Ashramam Gurukula', location: 'Bharanaganam', username: 'ashramam', password: 'Ashramam@2026', tag: 'Focus & Mindfulness' },
  { id: 8, name: 'St.Clare Gurukula', location: 'Poovathodu, Bharanaganam', username: 'stclare', password: 'StClare@2026', tag: 'Social Outreach' },
  { id: 9, name: 'Assisi Mount Gurukula', location: 'Melampara', username: 'assisimount', password: 'AssisiMount@2026', tag: 'Sports & Excellence' },
  { id: 10, name: 'Mitraniketan Boys Gurukula', location: 'Vagamon', username: 'assisivagamon', password: 'Mitraniketan@2026', tag: 'Residential Campus' },
  { id: 11, name: 'Thopramkudy Gurukula', location: 'Thopramkudy', username: 'thopramkudy', password: 'Thopramkudy@2026', tag: 'Digital & Technical' },
];

export const mockPosts = [
  {
    id: 1,
    institution_id: 1,
    institution_name: 'Liebhaus Gurukula',
    title: 'Welcome to the new academic year!',
    content: 'We are thrilled to welcome all new students to the Liebhaus Gurukula campus. Orientation will begin at 10:00 AM on Monday in the main auditorium. Please remember to bring your admission packets.',
    type: 'notice',
    created_at: new Date().toISOString(),
    hashtags: 'welcome,orientation,2026',
    media_url: null
  },
  {
    id: 2,
    institution_id: 2,
    institution_name: 'Bethsleeha Gurukula',
    title: 'Value Education Seminar',
    content: 'A mandatory seminar on Value Education will be held this Friday. All students are expected to attend and participate in the interactive sessions.',
    type: 'event',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    hashtags: 'valueEducation,seminar',
    media_url: null
  },
  {
    id: 3,
    institution_id: 3,
    institution_name: 'Pala Gurukula',
    title: 'Semester 1 Science Syllabus',
    content: 'The detailed syllabus for Semester 1 has been uploaded. Please download the attached PDF for your reference.',
    type: 'pdf',
    created_at: new Date(Date.now() - 172800000).toISOString(),
    hashtags: 'syllabus,science,sem1',
    media_url: '/mock/syllabus.pdf'
  }
];
