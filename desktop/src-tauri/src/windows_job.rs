//! Ties a spawned child process's lifetime to this process on Windows.
//!
//! Killing the child only from the `ExitRequested` handler in `lib.rs` isn't
//! enough: if this process dies without running that cleanup code (a crash,
//! "End Task" in Task Manager, `taskkill /F`, a debugger detach, ...) the
//! sidecar is orphaned and keeps running. A Windows Job Object with
//! `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` fixes that at the OS level: Windows
//! closes all of this process's handles (including the job handle) whenever
//! it exits for any reason, and that closure is what triggers the kill.

use windows::Win32::System::JobObjects::{
    AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
    SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
};
use windows::Win32::System::Threading::{OpenProcess, PROCESS_SET_QUOTA, PROCESS_TERMINATE};

/// Puts the process identified by `pid` into a new job object that is
/// configured to kill its member processes as soon as the job handle closes.
/// The returned `HANDLE` is intentionally never closed: it must stay open
/// for as long as this process is alive, and `HANDLE` being `Copy` means
/// letting it go out of scope here doesn't close it - Windows reclaims it
/// (and, per the job's limit, kills the sidecar) when this process exits.
pub fn kill_with_parent(pid: u32) -> windows::core::Result<()> {
    unsafe {
        let job = CreateJobObjectW(None, windows::core::PCWSTR::null())?;

        let mut info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            &info as *const _ as *const _,
            std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
        )?;

        let process = OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, false, pid)?;
        let assign_result = AssignProcessToJobObject(job, process);
        let _ = windows::Win32::Foundation::CloseHandle(process);
        assign_result?;
    }

    Ok(())
}
