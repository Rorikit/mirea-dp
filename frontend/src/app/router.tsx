import { useSyncExternalStore } from "react";
import {
  createBrowserRouter,
  Link,
  Navigate,
  NavLink,
  Outlet,
  useNavigate,
} from "react-router";
import {
  AdminMapPage,
  AdminPage,
  AdminSchedulePage,
  ImportPage,
  LoginPage,
  Protected,
  RecentScansPage,
  ScannerPage,
  StudentsPage,
  UsersPage,
} from "../pages/StaffPages";
import {
  HomePage,
  MapPage,
  MePage,
  RegisterPage,
  SchedulePage,
} from "../pages/PublicPages";
import {
  getStaffRole,
  logoutStaff,
  staffHome,
  subscribeToAuth,
  type StaffRole,
} from "../shared/api";

/* eslint-disable react-refresh/only-export-components -- router and layout belong together. */

function Layout() {
  const role = useSyncExternalStore(subscribeToAuth, getStaffRole, getStaffRole);
  const navigate = useNavigate();

  async function logout() {
    await logoutStaff();
    navigate("/", { replace: true });
  }

  return (
    <div className="app">
      <header>
        <Link className="brand" to={staffHome(role)}>ДП · 2026</Link>
        <nav aria-label="Основная навигация">
          {role === "ADMIN" && (
            <>
              <NavLink to="/admin">Панель</NavLink>
              <NavLink to="/admin/students">Студенты</NavLink>
              <NavLink to="/admin/users">Операторы</NavLink>
            </>
          )}
          {role === "OPERATOR" && (
            <>
              <NavLink to="/operator/scanner">Сканер</NavLink>
              <NavLink to="/operator/recent">Последние</NavLink>
            </>
          )}
          {role ? (
            <button className="nav-button" type="button" onClick={logout}>Выйти</button>
          ) : (
            <>
              <NavLink to="/schedule">Расписание</NavLink>
              <NavLink to="/map">Карта</NavLink>
              <NavLink to="/me">Мой QR</NavLink>
            </>
          )}
        </nav>
      </header>
      <main><Outlet /></main>
      <footer>РТУ МИРЭА · Москва · 2026</footer>
    </div>
  );
}

function HomeRoute() {
  const role = getStaffRole();
  return role ? <Navigate to={staffHome(role)} replace /> : <HomePage />;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const role = getStaffRole();
  return role ? <Navigate to={staffHome(role)} replace /> : children;
}

const secure = (element: React.ReactNode, roles: StaffRole[]) => (
  <Protected roles={roles}>{element}</Protected>
);
const publicOnly = (element: React.ReactNode) => <PublicOnly>{element}</PublicOnly>;

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: HomeRoute },
      { path: "register", element: publicOnly(<RegisterPage />) },
      { path: "me", element: publicOnly(<MePage />) },
      { path: "schedule", Component: SchedulePage },
      { path: "map", Component: MapPage },
      { path: "login", element: publicOnly(<LoginPage />) },
      {
        path: "operator/scanner",
        element: secure(<ScannerPage />, ["ADMIN", "OPERATOR"]),
      },
      {
        path: "operator/recent",
        element: secure(<RecentScansPage />, ["ADMIN", "OPERATOR"]),
      },
      { path: "admin", element: secure(<AdminPage />, ["ADMIN"]) },
      { path: "admin/imports", element: secure(<ImportPage />, ["ADMIN"]) },
      { path: "admin/students", element: secure(<StudentsPage />, ["ADMIN"]) },
      { path: "admin/users", element: secure(<UsersPage />, ["ADMIN"]) },
      {
        path: "admin/schedule",
        element: secure(<AdminSchedulePage />, ["ADMIN"]),
      },
      { path: "admin/map", element: secure(<AdminMapPage />, ["ADMIN"]) },
      {
        path: "*",
        element: (
          <section>
            <h1>Страница не найдена</h1>
            <Link to="/">Вернуться на главную</Link>
          </section>
        ),
      },
    ],
  },
]);
