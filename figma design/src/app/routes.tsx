import { createBrowserRouter } from "react-router";
import Landing from "./Landing";
import Login from "./Login";
import Signup from "./Signup";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Landing,
  },
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/signup",
    Component: Signup,
  },
]);
