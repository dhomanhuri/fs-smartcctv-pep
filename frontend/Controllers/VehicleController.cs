using System;
using System.Linq;
using System.Web.Mvc;
using MvcSmartCctv.Models;
using MvcSmartCctv.Services;

namespace MvcSmartCctv.Controllers
{
    public class VehicleController : BaseController
    {
        public ActionResult Index()
        {
            SetShell("vehicle");
            ViewBag.Title = "Vehicle Violation";

            var token = CurrentUser.AccessToken;
            var cameras = FastApiClient.GetCameras("vehicle", token);
            var violations = FastApiClient.GetViolations("vehicle", 100, token);
            var since24h = DateTime.Now.AddHours(-24);

            var vm = new DetectionViewModel
            {
                Category = "vehicle",
                PageTitle = "Vehicle Violation",
                PageDescription = "Deteksi penumpang di bak kendaraan pada zona kamera terkait.",
                AccentColor = "#B8021F",
                Cameras = cameras,
                Violations = violations,
                StatCams = cameras.Count,
                StatToday = violations.Count(v => v.CreatedAt >= since24h),
                StatOpen = violations.Count(v => v.IsCase && v.Status != "selesai"),
            };
            return View("~/Views/Shared/Detection.cshtml", vm);
        }
    }
}
