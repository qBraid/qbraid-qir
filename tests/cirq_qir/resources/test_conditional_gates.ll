; ModuleID = 'test_conditional_gates'
source_filename = "circuit-778bcda"

%Qubit = type opaque
%Result = type opaque

define void @main() #0 {
entry:
  call void @__quantum__rt__initialize(i8* null)
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__h__body(%Qubit* inttoptr (i64 1 to %Qubit*))
  %0 = call i1 @__quantum__qis__read_result__body(%Result* inttoptr (i64 1 to %Result*))
  br i1 %0, label %then, label %else

then:                                             ; preds = %entry
  call void @__quantum__qis__z__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  br label %continue

else:                                             ; preds = %entry
  call void @__quantum__qis__x__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  call void @__quantum__qis__x__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  br label %continue

continue:                                         ; preds = %else, %then
  %1 = call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %1, label %then1, label %else2

then1:                                            ; preds = %continue
  call void @__quantum__qis__z__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  br label %continue3

else2:                                            ; preds = %continue
  br label %continue3

continue3:                                        ; preds = %else2, %then1
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))
  %2 = call i1 @__quantum__qis__read_result__body(%Result* inttoptr (i64 1 to %Result*))
  br i1 %2, label %then4, label %else5

then4:                                            ; preds = %continue3
  call void @__quantum__qis__rz__body(double 5.000000e-01, %Qubit* inttoptr (i64 2 to %Qubit*))
  br label %continue6

else5:                                            ; preds = %continue3
  call void @__quantum__qis__x__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  call void @__quantum__qis__x__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  br label %continue6

continue6:                                        ; preds = %else5, %then4
  %3 = call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %3, label %then7, label %else8

then7:                                            ; preds = %continue6
  call void @__quantum__qis__rz__body(double 5.000000e-01, %Qubit* inttoptr (i64 2 to %Qubit*))
  br label %continue9

else8:                                            ; preds = %continue6
  br label %continue9

continue9:                                        ; preds = %else8, %then7
  call void @__quantum__rt__result_record_output(%Result* null, i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 2 to %Result*), i8* null)
  ret void
}

declare void @__quantum__rt__initialize(i8*)

declare void @__quantum__qis__h__body(%Qubit*)

declare i1 @__quantum__qis__read_result__body(%Result*)

declare void @__quantum__qis__z__body(%Qubit*)

declare void @__quantum__qis__x__body(%Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

declare void @__quantum__qis__rz__body(double, %Qubit*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="custom" "required_num_qubits"="3" "required_num_results"="3" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
