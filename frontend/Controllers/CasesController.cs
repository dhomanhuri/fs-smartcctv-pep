using System.Web.Mvc;
using MvcSmartCctv.Models;
using MvcSmartCctv.Services;

namespace MvcSmartCctv.Controllers
{
    public class CasesController : BaseController
    {
        public ActionResult Index(string filter)
        {
            SetShell("cases");
            ViewBag.Title = "Case Violation";

            if (string.IsNullOrEmpty(filter)) filter = "all";

            var rows = FastApiClient.GetCases(filter, CurrentUser.AccessToken);

            var vm = new CasesViewModel
            {
                ActiveFilter = filter,
                Rows = rows,
            };
            return View(vm);
        }

        [HttpPost]
        public ActionResult Promote(int id, string redirectUrl)
        {
            FastApiClient.PromoteToCase(id, CurrentUser.AccessToken);
            if (!string.IsNullOrEmpty(redirectUrl) && Url.IsLocalUrl(redirectUrl)) return Redirect(redirectUrl);
            return RedirectToAction("Index");
        }

        [HttpPost]
        public ActionResult UpdateStatus(int id, string status, string assignedToUserId, string redirectUrl)
        {
            FastApiClient.UpdateCaseStatus(id, status, assignedToUserId, CurrentUser.AccessToken);
            if (!string.IsNullOrEmpty(redirectUrl) && Url.IsLocalUrl(redirectUrl)) return Redirect(redirectUrl);
            return RedirectToAction("Index");
        }

        [HttpPost]
        public ActionResult AddNote(int id, string text, string redirectUrl)
        {
            if (!string.IsNullOrWhiteSpace(text))
            {
                FastApiClient.AddCaseNote(id, text, CurrentUser.AccessToken);
            }
            if (!string.IsNullOrEmpty(redirectUrl) && Url.IsLocalUrl(redirectUrl)) return Redirect(redirectUrl);
            return RedirectToAction("Index");
        }
    }
}
