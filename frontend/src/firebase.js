// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
// import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyB7ullSbw5n1eXZle07cZRTrV8V26H2NoU",
  authDomain: "private-class-vision.firebaseapp.com",
  projectId: "private-class-vision",
  storageBucket: "private-class-vision.firebasestorage.app",
  messagingSenderId: "852236568195",
  appId: "1:852236568195:web:857965a62d248fa4ed7db6",
  measurementId: "G-C58X9YSBED"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
// const analytics = getAnalytics(app);

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();