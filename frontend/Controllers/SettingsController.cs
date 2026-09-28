using System.Web.Mvc;
using MvcSmartCctv.Models;
using MvcSmartCctv.Services;

namespace MvcSmartCctv.Controllers
{
    public class SettingsController : BaseController
    {
        public ActionResult Index()
        {
            SetShell("settings");
            ViewBag.Title = "Pengaturan";

            var shell = ViewBag.Shell as ShellViewModel;
            ViewBag.IsAdmin = shell != null && shell.IsAdmin;

            var cameras = FastApiClient.GetCameras(null, CurrentUser.AccessToken);
            return View(cameras);
        }
    }
}
